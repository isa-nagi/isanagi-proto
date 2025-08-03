import copy
import importlib.util
import os
import re
import sys
from isana.semantic import (
    may_change_pc_absolute,
    may_change_pc_relative,
)


class Bits():
    def __init__(self, *args, **kwargs):
        self.offset = -1
        bit_slice = r"\s*(\d+)\s*:\s*(\d+)\s*"
        bit_index = r"\s*(\d+)\s*"
        if len(args) == 1 and isinstance(args[0], str):
            try:
                if m := re.match(r"^(\$\w+)\[([^\]]+)\]$", args[0]):
                    self.label = m.group(1)
                    bit_indices = m.group(2)
                    # TODO: verify bit range
                    if m2 := re.match(fr"^{bit_slice}$", bit_indices):
                        self.msb = int(m2.group(1))
                        self.lsb = int(m2.group(2))
                    elif m2 := re.match(fr"^{bit_index}$", bit_indices):
                        self.msb = int(m2.group(1))
                        self.lsb = int(m2.group(1))
                    else:
                        raise ValueError()
                    self.value = 0
                elif m := re.match(r"^(0x|0d)?([0-9a-f]+)\[([^\]]+)\]$", args[0]):
                    self.label = "#"
                    if m.group(1) == "0x":
                        base = 16
                    elif m.group(1) == "0d":
                        base = 10
                    else:
                        base = 2
                    self.value = int(m.group(2), base)
                    bit_indices = m.group(3)
                    # TODO: verify bit range
                    if m2 := re.match(fr"^{bit_slice}$", bit_indices):
                        self.msb = int(m2.group(1))
                        self.lsb = int(m2.group(2))
                    elif m2 := re.match(fr"^{bit_index}$", bit_indices):
                        self.msb = int(m2.group(1))
                        self.lsb = int(m2.group(1))
                    else:
                        raise ValueError()
                else:
                    raise ValueError()
            except ValueError:
                raise ValueError("binary() arguments syntax error: \"{}\"".format(args[0]))
        elif len(args) == 3 or len(args) == 4:
            self.label = args[0]
            self.msb = args[1]
            self.lsb = args[2]
            self.value = args[3] if len(args) == 4 else 0
        elif len(kwargs) > 0:
            self.label = kwargs.get('label', str())
            self.msb = kwargs.get('msb', -1)
            self.lsb = kwargs.get('lsb', -1)
            self.value = kwargs.get('value', 0)
        else:
            self.label = str()
            self.msb = -1
            self.lsb = -1
            self.value = 0

    def __repr__(self):
        return "{}:[{}:{}]={}".format(
            self.label,
            self.msb,
            self.lsb,
            self.value,
        )

    def size(self):
        return self.msb - self.lsb + 1

    def mask(self):
        return 2 ** self.size() - 1

    def pop_value(self, value):
        v = (value & self.mask()) << self.lsb
        nv = value >> self.size()
        return (v, nv)


class ISA():
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.endian = kwargs.pop('endian', "little")
        self.registers = kwargs.pop('registers')
        self.memories = kwargs.pop('memories')
        self.immediates = kwargs.pop('immediates')
        self.instructions = []
        self.instruction_aliases = []
        self.unknown_instructions = []
        instructions = kwargs.pop('instructions')
        for instr in instructions:
            if isinstance(instr, (InstructionAlias, PseudoInstruction)):
                self.instruction_aliases.append(instr)
            elif issubclass(instr, unknown_op):
                self.unknown_instructions.append(instr)
            else:
                self.instructions.append(instr)
        self._compiler = kwargs.pop('compiler', None)
        self.context = kwargs.pop('context')
        self._ctx = None
        for key, value in kwargs.items():
            setattr(self, key, value)

        # init after all argument set
        self.new_context()
        self._autofill_instructions_attribute()
        self._make_instruction_tree()
        self._make_decoder()
        if (type(self._compiler) is type(object)):
            self._compiler = self._compiler(self)

    @property
    def compiler(self):
        return self._compiler

    def is_opc_type(self, tp: str):
        return tp == "Opc"

    def is_reg_type(self, tp: str):
        for reg in self.registers:
            if tp == reg.label:
                return True
        return False

    def is_imm_type(self, tp: str):
        for imm in self.immediates:
            if tp == imm.label:
                return True
        return False

    def get_reg(self, tp: str, idx: int):
        group = None
        for group_ in self.registers:
            if tp == group_.label:
                group = group_
                break
        if group:
            for reg in group.regs:
                if idx == reg.idx:
                    return reg
        return None

    def get_reg_name(self, tp: str, idx: int, alias=True):
        reg = self.get_reg(tp, idx)
        if reg:
            if alias and len(reg.aliases) > 0:
                return reg.aliases[0]
            else:
                return reg.label
        return "<{}:{}>".format(idx, tp)

    def get_imm_str(self, tp: str, value: int, instr: 'Instruction'):
        try:
            s = "{} <{}>".format(str(hex(value)), hex(instr.target_addr()))
        except NotImplementedError:
            s = str(hex(value))
        return s

    def get_param_obj(self, name: str, instr):
        param = instr.params.outputs.get(name, None) or instr.params.inputs.get(name, None)
        if self.is_reg_type(param.type_):
            for reg in self.registers:
                if param.type_ == reg.label:
                    return reg
        elif self.is_imm_type(param.type_):
            for imm in self.immediates:
                if param.type_ == imm.label:
                    return imm
        else:
            return None
        return None

    def param_str(self, param, alias=True):
        if self.is_opc_type(param.type_):
            s = param.label
        elif self.is_reg_type(param.type_):
            s = self.get_reg_name(param.type_, param.number, alias=alias)
        elif self.is_imm_type(param.type_):
            s = self.get_imm_str(param.type_, param.value, param.instr)
        else:
            s = "{}:{}".format(param.label, param.type_)
        return s

    def decode(self, data: bytes, addr: int | None = None):
        return self._decode0(data, addr=addr)

    def _decode_simple(self, data: bytes, addr: int | None = None):
        # simple opecode match
        instr = None
        for instr0 in self.instructions + self.unknown_instructions:
            instr0 = instr0()
            value0 = instr0.value_swap_endian(data, self.endian)
            instr0.isa = self
            if instr0.match_opecode(value0):
                instr = instr0
                value = value0
                break
        else:
            instr = unknown_op()
            value = int.from_bytes(data, byteorder=self.endian)
            instr.isa = self
        instr.decode(value, addr=addr)
        return instr

    _decode0 = _decode_simple

    def assemble(self, s):
        alias_ops = re.split(r"\s*,?\s+", s)
        instr = next(filter(lambda x: x.opn == alias_ops[0], self.instructions), None)
        if instr is None:
            return None
        dstnode = []
        instr_ops = re.split(r"\s*,?\s+", instr.asm.pattern)
        dstnode.append(instr.__name__.upper())
        alias_ops = [op.strip("()")for op in alias_ops][1:]
        instr_ops = [op.strip("()")for op in instr_ops][1:]
        instr_op_labels = [op if op[0] != "$" else op[1:] for op in instr_ops]
        params = []
        for prm in list(instr.prm.outputs.keys()) + list(instr.prm.inputs.keys()):
            if prm not in params:
                params.append(prm)
        for i, prm in enumerate(params):
            idx = instr_op_labels.index(prm)
            if alias_ops[idx][0] == "$":
                label = alias_ops[idx][1:]
                prmobj = self.get_param_obj(instr_ops[idx][1:], instr)
                cls = prmobj.label
                if isinstance(prmobj, Immediate):
                    if may_change_pc_relative(instr):
                        cls = "Br" + cls
                dstnode.append("{}:${}".format(cls, label))
            else:
                dstnode.append(alias_ops[idx].upper())
        return dstnode

    def new_context(self):
        ctx = self.context(
            registers=copy.deepcopy(self.registers),
            memories=copy.deepcopy(self.memories),
            # immediates=copy.deepcopy(self.immediates),
        )
        self._ctx = ctx

    def execute(self, addr=None):
        if addr is None:
            addr = self._ctx.PC.pc
        value = self._ctx.Mem.read(32, addr)
        data = value.to_bytes(4, self.endian)
        ins = self.decode(data, addr=addr)
        self._ctx.pre_semantic()
        ins.semantic(self._ctx, ins)
        self._ctx.post_semantic(ins)

    def _autofill_instructions_attribute(self):
        for instr in self.instructions:
            instr._new_param_attribute(instr, self)
            if m := may_change_pc_absolute(instr):
                expr = m
                expr = re.sub(r'ins\.(\w+)', r'self.params.inputs["\1"]', expr)
                # print("A", f'"{m}"', f'"{expr}"', instr)
                # [TODO] implement target_addr() for pc-absolute
            elif m := may_change_pc_relative(instr):
                expr = m
                expr = re.sub(r'ins\.(\w+)', r'self.params.inputs["\1"].value', expr)
                expr = f'self.addr + {expr}'
                # print("R", f'"{m}"', f'"{expr}"', instr)
                def new_target_addr(expr):
                    def target_addr(self):
                        return eval(expr)
                    return target_addr
                instr.target_addr = new_target_addr(expr)

    def _make_instruction_tree(self):
        done = list()
        rest = self.instructions[:]
        instr_tree = {instr: InstructionTree(instr) for instr in rest}
        while rest:
            instr = rest.pop(0)
            parent = instr.__bases__[0]
            if issubclass(parent, Instruction) and parent.isa is None:
                parent.isa = instr.isa
            instr_tree.setdefault(parent, InstructionTree(parent))
            instr_tree[instr].parent = instr_tree[parent]
            if instr_tree[instr] not in instr_tree[parent].children:
                instr_tree[parent].children.append(instr_tree[instr])
            done.append(instr)
            if parent not in done and parent != object:
                rest.append(parent)
        root = instr_tree[Instruction]
        root.parent = None
        self.instruction_tree = root

    def _walk_instruction_tree_by_depth(self):
        pass
        def _walk(node, visited):
            visited.append(node)
            yield node, True  # go foward
            for child in node.children:
                if child not in visited:
                    for _ in _walk(child, visited): yield _  # noqa
            yield node, False  # go back

        # rest = self.instruction_tree.children[:]
        rest = [self.instruction_tree]
        visited = []
        while len(rest) > 0:
            first = rest[0]
            for _ in _walk(first, visited): yield _  # noqa
            for f in visited:
                if f in rest:
                    rest.remove(f)

    def _make_decoder(self):
        depth = 0
        for node, gofoward in self._walk_instruction_tree_by_depth():
            depth += 1 if gofoward else - 1
            node.depth = depth
            if node.instr == Instruction:
                continue
            instr = node.instr
            if gofoward:
                pattern = ''
                bits_sum = 0
                if instr.opc is None:
                    node.pattern = 'X' * instr.bin.bitsize
                    continue
                for bits in reversed(instr.bin.bitss):
                    if bits.label == "$opc":
                        bits_value = (instr.opc >> bits_sum) & (2 ** (bits.size()) - 1)
                        for bi in range(bits.size()):
                            bit = bits_value & 1
                            pattern += str(bit)
                            bits_value >>= 1
                    else:
                        pattern += '*' * bits.size()
                    bits_sum += bits.size()
                node.pattern = pattern[::-1]
            else:
                n_ptn = node.pattern
                p_ptn = node.parent.pattern
                max_bits = max(len(n_ptn), len(p_ptn))
                if not p_ptn:
                    p_ptn = 'X' * max_bits
                if len(p_ptn) < len(n_ptn):
                    p_ptn = 'X' * (len(n_ptn) - len(p_ptn)) + p_ptn
                if len(n_ptn) < len(p_ptn):
                    n_ptn = '*' * (len(p_ptn) - len(n_ptn)) + n_ptn
                new_p_ptn = ''
                for i in range(max_bits):
                    if p_ptn[i] == 'X':
                        new_p_ptn += n_ptn[i]
                    else:
                        if n_ptn[i] == '*':
                            new_p_ptn += '*'
                        elif p_ptn[i] != n_ptn[i]:
                            new_p_ptn += '*'
                        else:
                            new_p_ptn += p_ptn[i]
                node.parent.pattern = new_p_ptn
                mask = 0
                value = 0
                for i, s in enumerate(node.pattern[::-1]):
                    bit = 2 ** i
                    if s != '*':
                        mask += bit
                    if s == '1':
                        value += bit
                node.pattern_mask = mask
                node.pattern_value = value
        # check duplicates
        # for node, gofoward in self._walk_instruction_tree_by_depth():
        #     if gofoward and node.depth < 3:
        #         print('{:19s} {:>32s} {:032b} {:032b}'.format(
        #             ('  ' * node.depth) + node.instr.__name__,
        #             node.pattern,
        #             node.pattern_mask,
        #             node.pattern_value,
        #         ))
        self._decode0 = self._decode_tree

    def _decode_tree(self, data: bytes, addr: int | None = None):
        ranks = list()
        ranks.append(self.instruction_tree.children[:])
        instr = None
        while True:
            if len(ranks) == 0:
                break
            nodes = ranks[-1]
            if len(nodes) == 0:
                ranks.pop()
                continue
            node = nodes.pop(0)
            # instr0 = node.instr()
            # value0 = instr0.value_swap_endian(data, self.endian)
            instr0 = node.instr
            value0 = instr0.value_swap_endian(instr0, data, self.endian)
            if len(node.children) > 0:
                if not node.match_value(value0):
                    continue
                ranks.append(node.children[:])
                continue
            else:
                if instr0.match_opecode(instr0, value0):
                    instr = instr0()
                    value = value0
                    break
        if instr is None:
            for instr0 in self.unknown_instructions:
                instr0 = instr0
                value0 = instr0.value_swap_endian(instr0, data, self.endian)
                if instr0.match_opecode(instr0, value0):
                    instr = instr0()
                    value = value0
                    break
            else:
                instr = unknown_op()
                value = int.from_bytes(data, byteorder=self.endian)
                instr.isa = self
        instr.decode(value, addr=addr)
        return instr


class Context():
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.registers = kwargs.get('registers')
        self.memories = kwargs.get('memories')
        # self.immediates = kwargs.pop('immediates')

    def __getattr__(self, key):
        if isinstance(key, str):
            for x in self.registers:
                if key == x.label:
                    return x
            for x in self.memories:
                if key == x.label:
                    return x
        return super().__getattr__(key)

    def pre_semantic(self):
        pass

    def post_semantic(self):
        pass


class RegisterGroup():
    def __init__(self, label: str, **kwargs):
        self.label = label
        self.width = kwargs.get('width')
        self.regs = copy.deepcopy(kwargs.get('regs'))
        for i, reg in enumerate(self.regs):
            reg.group = self
            reg.idx = i

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < len(self.regs):
                return self.regs[key].value
        raise ValueError()

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key < len(self.regs):
                self.regs[key].value = value
                return
        raise ValueError()

    def __getattr__(self, key):
        if isinstance(key, str) and 'regs' in self.__dict__:
            for reg in self.regs:
                if key == reg.label:
                    return reg.value
        return super().__getattr__(key)

    def __setattr__(self, key, value):
        if isinstance(key, str) and 'regs' in self.__dict__:
            for reg in self.regs:
                if key == reg.label:
                    reg.value = value
                    return
        super().__setattr__(key, value)

    def __iter__(self):
        yield from self.regs

    def max_reg_number(self):
        return max([reg.number for reg in self.regs])

    def get_obj(self, key):
        for reg in self.regs:
            if key == reg.label:
                return reg
        return None


class Register():
    def __init__(self, number: int, label: str, *args, **kwargs):
        self.group = None
        self.number = number
        self.label = label
        self.aliases = args
        self.is_callee_saved = kwargs.get('callee', False)
        self.is_caller_saved = kwargs.get('caller', False)
        self.is_zero = kwargs.get('zero', False)
        self.is_arg = kwargs.get('arg', False)
        self.is_ret = kwargs.get('ret', False)
        self.is_return_address = kwargs.get('ra', False)
        self.is_stack_pointer = kwargs.get('sp', False)
        self.is_frame_pointer = kwargs.get('fp', False)
        self.is_global_pointer = kwargs.get('gp', False)
        self.is_pc = kwargs.get('pc', False)
        self.idx = kwargs.get('idx', number)
        self.dwarf_number = kwargs.get('dwarf', number)
        self.value = 0

    @property
    def attrs(self):
        attrs = [k[3:] for k in self.__dict__ if k[:3] == 'is_' and self.__dict__[k]]
        return attrs


class Memory():
    def __init__(self, label: str, **kwargs):
        self.label = label
        self.width = kwargs.get('width')
        self._byte_memory = dict()

    def read(self, bits: int, addr: int):
        if bits % 8 == 0:
            value = 0
            for bi in range(bits // 8):
                # TODO: Memory should return X value if not initialized?
                if bi in self._byte_memory:
                    value += self._byte_memory[addr + bi] << (bi * 8)
                else:
                    value += 0
            return value
        raise ValueError()

    def write(self, bits: int, addr: int, value):
        if bits % 8 == 0:
            for bi in range(bits // 8):
                self._byte_memory[addr + bi] = value & 0xff
                value = value >> 8
            return
        raise ValueError()


class Immediate():
    def __init__(self, label: str, **kwargs):
        self.label = label
        self.width = kwargs.get('width')
        self.offset = kwargs.get('offset', 0)
        self.enums = kwargs.get('enums', None)

    def cast(self, value):
        return value


class ImmU(Immediate):
    def __init__(self, label: str, **kwargs):
        super().__init__(label, **kwargs)


class ImmS(Immediate):
    def __init__(self, label: str, **kwargs):
        super().__init__(label, **kwargs)

    def signed(self, value):
        msb = self.width + self.offset
        if value & (1 << (msb - 1)):
            value = value - (1 << msb)
        return value

    def cast(self, value):
        return self.signed(value)


class Instruction():
    isa = None

    opc = None
    opn = None
    prm = None
    asm = None
    bin = None

    # Only one of jump, branch, call, tail or return can be True.
    is_jump = False
    is_branch = False
    is_call = False
    is_tail = False
    is_return = False

    is_indirect = False

    is_load = False
    is_store = False
    is_pop = False
    is_push = False

    has_sideeffect = False

    def __init__(self):
        # self.isa = None
        self.addr = None
        self._operands = dict()
        self._pseudo_instrs = list()
        self._disasm_str = str()
        self._value = int()
        self._init_params()

    def _init_params(self):
        if hasattr(self.__class__, 'params'):
            params = self.__class__.params
            obj_params = InstructionParameters(isa=self.__class__.isa)
            for k, v in params.opecodes.items():
                param = copy.deepcopy(v)
                param.instr = self
                obj_params.opecodes[k] = param
            for k, v in params.outputs.items():
                param = copy.deepcopy(v)
                param.instr = self
                obj_params.outputs[k] = param
            for k, v in params.inputs.items():
                param = copy.deepcopy(v)
                param.instr = self
                obj_params.inputs[k] = param
            self.params = obj_params
        else:
            obj_params = InstructionParameters(isa=self.__class__.isa)
            self.params = obj_params

    def __repr__(self):
        s = "Instruction({})"
        indent = ""
        prms = " ".join([
            indent + repr(self.opn),
            indent + repr(self.params.outputs),
            indent + repr(self.params.inputs),
        ])
        return s.format(prms)

    def __getattr__(self, key):
        if isinstance(key, str):
            param = None
            if key in self.params.inputs:
                param = self.params.inputs[key]
            elif key in self.params.outputs:
                param = self.params.outputs[key]
            if param:
                if self.isa.is_reg_type(param.type_):
                    return param.number
                elif self.isa.is_imm_type(param.type_):
                    return param.value
        return super().__getattr__(key)

    def __setattr__(self, key, value):
        if isinstance(key, str) and 'params' in self.__dict__ and key in self.params.outputs:
            self.params.outputs[key].value = value
            return
        super().__setattr__(key, value)

    def semantic(self, ctx, ins):
        pass

    def pipeline(self):
        pass

    @property
    def value(self):
        return self._value

    @property
    def bitsize(self):
        return self.bin.bitsize

    @property
    def bytesize(self):
        return self.bin.bytesize

    @property
    def opecode(self):
        return self.params.opecodes

    @property
    def operands(self):
        # return self.asm.operands
        if not self.isa:
            return None
        outlist = list()
        for ast in self.asm.ast:
            if ast == '$opn':
                opecode0 = list(self.params.opecodes.values())[0]
                outlist += [opecode0]
            elif ast[0] == '$':
                label = ast[1:]
                if label in self.params.outputs:
                    param = self.params.outputs[label]
                    outlist += [param]
                elif label in self.params.inputs:
                    param = self.params.inputs[label]
                    outlist += [param]
                else:
                    outlist += [InstructionParam()]
                    # raise ValueError()
            else:
                pass
        return outlist

    def target_addr(self):
        # jump/branch/call/tail target address
        # TODO: generate from semantic
        raise NotImplementedError()

    def value_swap_endian(self, value: bytes, endian: str):
        if not self.bin:
            return None
        value_ = value[:self.bin.bytesize]
        if endian == "big":
            # swap to little endian
            value_ = reversed(value_)
        new_value = int.from_bytes(value_, byteorder=endian)
        return new_value

    def match_opecode(self, value: int):
        bitvalue = 0
        for bits in reversed(self.bin.bitss):
            poped_value, value = bits.pop_value(value)
            if bits.label == "$opc":
                bitvalue += poped_value
        if bitvalue == self.opc:
            return True
        return False

    def _new_param_attribute(cls, isa):
        if not cls.bin:
            raise Exception(f"'{cls.__name__}' don't have 'bin'")
        if not cls.prm:
            raise Exception(f"'{cls.__name__}' don't have 'prm'")
        cls.isa = isa
        cls.params = InstructionParameters(isa=isa)
        for label in cls.prm.opecodes:
            tp = cls.prm.opecodes[label]
            cls.params.opecodes.setdefault(label, cls._make_param(cls, label, tp))
        for label in cls.prm.outputs:
            tp = cls.prm.outputs[label]
            cls.params.outputs.setdefault(label, cls._make_param(cls, label, tp))
        for label in cls.prm.inputs:
            tp = cls.prm.inputs[label]
            cls.params.inputs.setdefault(label, cls._make_param(cls, label, tp))

    def decode(self, value: int, addr: int | None = None):
        if not self.bin:
            return None
        self._value = value
        self.addr = addr if addr is not None else 0
        for label in self.prm.opecodes:
            tp = self.prm.opecodes[label]
            self.params.opecodes.setdefault(label, self._make_param(label, tp))
        for label in self.prm.outputs:
            tp = self.prm.outputs[label]
            self.params.outputs.setdefault(label, self._make_param(label, tp))
        for label in self.prm.inputs:
            tp = self.prm.inputs[label]
            self.params.inputs.setdefault(label, self._make_param(label, tp))
        for bits in reversed(self.bin.bitss):
            poped_value, value = bits.pop_value(value)
            if bits.label.startswith("$"):
                label = bits.label[1:]
                if label in self.prm.opecodes:
                    # key = 'opecodes'
                    tp = self.prm.opecodes[label]
                    param = self.params.opecodes[label]
                    self._add_value(param, tp, poped_value)
                if label in self.prm.outputs:
                    # key = 'outputs'
                    tp = self.prm.outputs[label]
                    param = self.params.outputs[label]
                    self._add_value(param, tp, poped_value)
                if label in self.prm.inputs:
                    # key = 'inputs'
                    tp = self.prm.inputs[label]
                    param = self.params.inputs[label]
                    self._add_value(param, tp, poped_value)
        for label, param in self.params.inputs.items():
            self._cast_value(param)

    def _make_param(self, label: str, tp: str):
        param = InstructionParam()
        param.instr = self
        param.label = label
        param.type_ = tp
        return param

    def _add_value(self, param, tp: str, poped_value: int):
        if self.isa.is_opc_type(tp):
            param.value = param.value if param.value is not None else 0
            param.value += poped_value
        elif self.isa.is_reg_type(tp):
            param.number = param.number if param.number is not None else 0
            param.number += poped_value
        elif self.isa.is_imm_type(tp):
            param.value = param.value if param.value is not None else 0
            param.value += poped_value
        # return param

    def _cast_value(self, param):
        for immtype in self.isa.immediates:
            if immtype.label == param.type_:
                param.value = immtype.cast(param.value)

    def disassemble(self):
        if not self.isa:
            return None
        isa = self.isa
        outstr = str()
        outparam = list()
        for ast in self.asm.ast:
            if ast == '$opn':
                outstr += self.opn
                outparam += [self.opn]
            elif ast[0] == '$':
                label = ast[1:]
                if label in self.params.outputs:
                    param = self.params.outputs[label]
                    outstr += isa.param_str(param)
                    outparam += [param]
                elif label in self.params.inputs:
                    param = self.params.inputs[label]
                    outstr += isa.param_str(param)
                    outparam += [param]
                else:
                    outstr += ast
                    outparam += [ast]
            else:
                outstr += ast
                outparam += [ast]
        self._disasm_str = outstr
        self._disasm_param = outparam
        return outstr

    def semantic_str(self):
        import ast
        import inspect
        import textwrap
        code = inspect.getsource(self.semantic)
        code = textwrap.dedent(code)
        s = ast.unparse(ast.parse(code).body[0].body)
        s = s.replace('ctx.', '')
        s = s.replace('ins.', '')
        # s = textwrap.indent(s, '  ')
        return s

    def bitfield_wavedrom(self):
        s = ['{"reg": [']
        for bits in reversed(self.bin.bitss):
            if bits.label == '$opc':
                s += ['{{"bits": {}, "name": "{}", "attr": {}}},'.format(
                    bits.size(),
                    "{}[{}]".format(
                        bits.label[1:],
                        "{}".format(bits.msb) if bits.msb == bits.lsb else "{}:{}".format(bits.msb, bits.lsb),
                    ),
                    (self.opc >> bits.lsb) & (2 ** (bits.msb - bits.lsb + 1) - 1),
                )]
            else:
                s += ['{{"bits": {}, "name": "{}"}},'.format(
                    bits.size(),
                    "{}[{}]".format(
                        bits.label[1:],
                        "{}".format(bits.msb) if bits.msb == bits.lsb else "{}:{}".format(bits.msb, bits.lsb),
                    )
                )]
        s[-1] = s[-1][:-1]  # remove last comma
        # s += '], "config": {"hspace": "width"}}'
        s += ['], "config": {{"bits": {}}} }}'.format(
            self.bin.bitsize,
        )]
        # s += [']}']
        s = '\n'.join(s)
        # s = textwrap.indent(s, '  ')
        return s


class unknown_op(Instruction):
    opn = "unknown_op"


class InstructionTree():
    def __init__(self, instr):
        self.instr = instr
        self.parent = None
        self.children = list()
        self.depth = -1
        self.pattern = ''
        self.pattern_mask = int()
        self.pattern_value = int()

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            self.instr.__name__,
        )

    def __repr__(self):
        return self.__str__()

    def match_value(self, value):
        masked_value = value & self.pattern_mask
        if masked_value == self.pattern_value:
            return True
        return False


class InstructionParameters():
    def __init__(self, isa=None):
        self.opecodes = InstructionParamDict(isa=isa)
        self.outputs = InstructionParamDict(isa=isa)
        self.inputs = InstructionParamDict(isa=isa)


class InstructionParamDict(dict):
    def __init__(self, *args, **kwargs):
        isa = kwargs.pop('isa')
        super().__init__(*args, **kwargs)
        self.isa = isa

    @property
    def regs(self):
        regs = list()
        for param in self.values():
            if self.isa.is_reg_type(param.type_):
                regs.append(param)
        return regs


class InstructionParam():
    def __init__(self):
        self.instr = None
        self.label = str()
        self.type_ = str()
        self.number = None
        self.value = None
        self.is_input = False
        self.is_output = False
        self.dataflow_src = None

    def __repr__(self):
        return "{}:{}=<{},{}>".format(
            self.label,
            self.type_,
            self.number,
            self.value,
        )

    def is_opc(self, isa):
        pass

    def is_reg(self, isa):
        pass

    def is_imm(self, isa):
        pass

    def is_symbol(self, isa):
        pass


class InstructionAssembly():
    def __init__(self, ptn: str):
        self.pattern = ptn
        self.ast = self.make_ast(ptn)

    def make_ast(self, ptn: str):
        astptns = re.split(r"(\$\w+)", ptn)
        asts = list()
        for astptn in astptns:
            if astptn == '':
                continue
            asts.append(astptn)
        return asts

    @property
    def operands(self):
        return [x for x in self.ast if x[0] == "$"]


class InstructionBinary():
    def __init__(self, ptn: str):
        self.bitss = self.make_bits(ptn)

    def __repr__(self):
        return ', '.join([repr(b) for b in self.bitss])

    def make_bits(self, ptn: str):
        bitptns = re.split(r"\s*,\s*", ptn)
        bitss = list()
        for bitptn in bitptns:
            bitss.append(Bits(bitptn))
        offset = 0
        for bits in reversed(bitss):
            bits.offset = offset
            offset += bits.size()
        return bitss

    @property
    def bitsize(self):
        if not self.bitss:
            return 0
        size = 0
        for bits in self.bitss:
            size += bits.msb - bits.lsb + 1
        return size

    @property
    def bytesize(self):
        return (self.bitsize + 7) // 8


def parameter(outputs: str, inputs: str) -> list[tuple[str, str]]:
    params = InstructionParameters()
    params.opecodes['opc'] = "Opc"
    if outputs != "":
        args = re.split(r"\s*,\s*", outputs)
        for arg in args:
            if m := re.match(r"(\w+)\s*:\s*(\w+)", arg):
                label, type_ = m.groups()
                params.outputs[label] = type_
            else:
                raise ValueError("Parse Error: Instruction Parameter: {}".format(
                    outputs
                ))

    if inputs != "":
        args = re.split(r"\s*,\s*", inputs)
        for arg in args:
            if m := re.match(r"(\w+)\s*:\s*(\w+)", arg):
                label, type_ = m.groups()
                params.inputs[label] = type_
            else:
                raise ValueError("Parse Error: Instruction Parameter: {}".format(
                    inputs
                ))

    return params


def assembly(ptn: str):
    asmops = InstructionAssembly(ptn)
    return asmops


def binary(ptn: str):
    bits = InstructionBinary(ptn)
    return bits


# ---- Instruction semantic utility ----

def signed(bits: int, value: int):
    sign = (1 << (bits - 1)) & value
    if sign:
        value = value - (1 << bits)
    return value


def unsigned(bits: int, value: int):
    return value & (2 ** bits - 1)


def s32(value: int):
    return signed(32, value)


def u32(value: int):
    return unsigned(32, value)


def compare(ctx, lhs: int, rhs: int):
    raise NotImplementedError()


# ----
class InstructionAlias():
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class PseudoInstruction():
    def __init__(self, src, dst, **kwargs):
        self.src = src
        self.dst = dst
        for k, v in kwargs.items():
            setattr(self, k, v)


# ----
def load_isa(isa_dir):
    try:
        isa_dir = isa_dir.rstrip(os.sep)
        isa_dir_basename = os.path.basename(isa_dir)
        isa_fpath = os.path.join(isa_dir, "isa.py")
        parent_dir = os.path.abspath(os.path.dirname(isa_dir))
        module_name = f"{isa_dir_basename}.isa"
        sys.path.append(parent_dir)
        spec = importlib.util.spec_from_file_location(module_name, isa_fpath)
        isa = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = isa
        spec.loader.exec_module(isa)
    except Exception:
        raise Exception("ISA model load failure")
    return isa.isa
