from .elf import SectionHeader, SymbolTable
from isana.isa import Instruction
import re
import sys


class Operator():
    def __init__(self):
        self.ins = None
        self.block = None
        self.data_srcs = list()
        self.data_dsts = list()
        # self.cyclic_data_srcs = list()
        # self.cyclic_data_dsts = list()

    def __repr__(self):
        if self.ins:
            # return self.ins.disassemble()
            return self._disassemble()
        return str(self)

    @property
    def addr(self):
        return self.ins.addr

    @property
    def binary(self):
        if self.ins:
            return self.ins.value
        return 0

    @property
    def size(self):
        if self.ins:
            return self.ins.bytesize
        raise NotImplementedError()

    def to_json(self):
        d = {
            'id': id(self),
            'addr': self.addr,
            'binary': self.binary,
            'ins': [
                {
                    'asm': self.ins.isa.param_str(p),
                    'type': p.type_,
                } for p in self.ins.operands],
            'block': id(self.block),
            'data_srcs': id(self.data_srcs),
            'data_dsts': id(self.data_dsts),
        }
        return d

    def regs_used_in(self, op):
        for reg0 in self.ins.params.outputs.regs:
            for reg1 in op.ins.params.inputs.regs:
                reg0_v = self.ins.isa.get_reg_name(reg0.type_, reg0.number)
                reg1_v = self.ins.isa.get_reg_name(reg1.type_, reg1.number)
                if reg0_v == reg1_v:
                    return True
        return False

    def regs_overwritten_by(self, op):
        for reg0 in self.ins.params.outputs.regs:
            for reg1 in op.ins.params.outputs.regs:
                reg0_v = self.ins.isa.get_reg_name(reg0.type_, reg0.number)
                reg1_v = self.ins.isa.get_reg_name(reg1.type_, reg1.number)
                if reg0_v == reg1_v:
                    return True
        return False

    def _disassemble(self):
        if not self.ins.isa:
            return None
        outstr = str()
        outparam = list()
        for ast in self.ins.asm.ast:
            if ast == '$opn':
                outstr += self.ins.opn
                outparam += [self.ins.opn]
            elif ast[0] == '$':
                label = ast[1:]
                if label in self.ins.params.outputs:
                    param = self.ins.params.outputs[label]
                    outstr += self._param_str(param)
                    outparam += [param]
                elif label in self.ins.params.inputs:
                    param = self.ins.params.inputs[label]
                    outstr += self._param_str(param)
                    outparam += [param]
                else:
                    outstr += ast
                    outparam += [ast]
            else:
                outstr += ast
                outparam += [ast]
        self.ins._disasm_str = outstr
        self.ins._disasm_param = outparam
        return outstr

    def _param_str(self, param):
        if self.ins.isa.is_opc_type(param.type_):
            s = param.label
        elif self.ins.isa.is_reg_type(param.type_):
            s = self.ins.isa.get_reg_name(param.type_, param.number)
        elif self.ins.isa.is_imm_type(param.type_):
            s = self._get_imm_str(param.type_, param.value, param.instr)
        else:
            s = "{}:{}".format(param.label, param.type_)
        return s

    def _get_imm_str(self, tp: str, value: int, instr: Instruction):
        try:
            tgt_addr = instr.target_addr()
            tgt_block = None
            tgt_offset = 0
            disobj = self.block.disobj
            for block in disobj.blocks:
                if block.addr <= tgt_addr and tgt_addr < block.addr + block.size:
                    if len(block.symbols) > 0:
                        tgt_block = block
                        tgt_offset = tgt_addr - block.addr
            fs = ""
            if tgt_block:
                sign = "+" if tgt_offset >= 0 else "-"
                fs = ": {}{}0x{:x}".format(tgt_block.label, sign, abs(tgt_offset))
            s = "{} <{}{}>".format(str(hex(value)), hex(tgt_addr), fs)
        except NotImplementedError:
            s = str(hex(value))
        return s


def escape_label(label):
    return re.sub(r"\W", "_", label)


class BasicBlock():
    def __init__(self):
        self.disobj = None
        self.symbols = list()
        self.operators = list()
        self.jump_srcs = list()
        self.jump_tgts = list()
        self.cyclic_jump_srcs = list()
        self.cyclic_jump_tgts = list()
        self.outer_jump_srcs = list()
        self.outer_jump_tgts = list()
        self.addr = int()
        self.size = int()
        self.function = None
        self.rank = -1

    @property
    def label(self):
        return self.labels[0]

    @property
    def label_escape(self):
        return escape_label(self.label)

    @property
    def labels(self):
        if len(self.symbols) == 0:
            return ["<unlabeled block>"]
        labels = [st.name for st in self.symbols]
        return labels

    @property
    def jump_srcs_in_function(self):
        if not self.function:
            return None
        return [b for b in self.jump_srcs if b.isin(self.function)]

    def to_json(self):
        d = {
            'id': id(self),
            'symbols': [st.name for st in self.symbols],  # TODO
            'operators': [op.to_json() for op in self.operators],
            'jump_srcs': [id(b) for b in self.jump_srcs],
            'jump_tgts': [id(b) for b in self.jump_tgts],
            'addr': self.addr,
            'size': self.size,
            'function': id(self.function),
            'rank': self.rank,
        }
        return d

    def walk_blocks_by_depth(self):
        def _walk(block, visited):
            visited.append(block)
            yield block, True  # go foward
            for child in block.jump_tgts:
                if child not in visited:
                    for _ in _walk(child, visited): yield _  # noqa
            yield block, False  # go back

        rest = [self]
        visited = []
        while len(rest) > 0:
            first = rest[0]
            for _ in _walk(first, visited): yield _  # noqa
            for b in visited:
                if b in rest:
                    rest.remove(b)

    def isin(self, obj):
        if isinstance(obj, Function):
            return self.function == obj
        raise ValueError()


class Function():
    def __init__(self):
        self.symbols = list()
        self.blocks = list()
        self.call_srcs = list()
        self.call_tgts = list()
        self.cyclic_call_srcs = list()
        self.cyclic_call_tgts = list()
        self.addr = int()
        self.size = int()

    @property
    def label(self):
        return self.labels[0]

    @property
    def label_escape(self):
        return escape_label(self.label)

    @property
    def labels(self):
        if len(self.blocks) == 0:
            if len(self.symbols) == 0:
                return ["<unlabeled block>"]
            else:
                labels = [st.name for st in self.symbols]
                return labels
        return [self.blocks[0].label]

    @property
    def max_rank(self):
        if self.blocks:
            return max([b.rank for b in self.blocks])
        return -1

    @property
    def max_depth(self):
        return self.max_rank

    @property
    def operators(self):
        for block in self.blocks:
            for op in block.operators:
                yield op

    def to_json(self):
        d = {
            'id': id(self),
            'symbols': [st.name for st in self.symbols],  # TODO
            # 'blocks': [b.to_json() for b in self.blocks],
            'blocks': [id(b) for b in self.blocks],
            'call_srcs': [id(f) for f in self.call_srcs],
            'call_tgts': [id(f) for f in self.call_tgts],
            'addr': self.addr,
            'size': self.size,
        }
        return d

    def walk_blocks_by_depth(self):
        def _walk(block, visited):
            visited.append(block)
            yield block, True  # go foward
            for child in block.jump_tgts:
                if child not in visited and child.function == self:
                    for _ in _walk(child, visited): yield _  # noqa
            yield block, False  # go back

        if len(self.blocks) > 0:
            rest = self.blocks[:]
            visited = []
            while len(rest) > 0:
                first = rest[0]
                for _ in _walk(first, visited): yield _  # noqa
                for b in visited:
                    if b in rest:
                        rest.remove(b)

    def walk_blocks_by_rank(self):
        # TODO: sort blocks to have the same cfg order
        blocks = self.blocks
        blocks = sorted(blocks, key=lambda b: b.rank)
        for block in blocks:
            yield block

    def walk_blocks_all_routes_by_depth(self):
        def _walk(block, visited, depth):
            new_visited = visited + [block]
            yield block, True  # go foward
            for child in block.jump_tgts:
                if child not in new_visited and child.function == self:
                    for _ in _walk(child, new_visited, depth + 1): yield _  # noqa
            yield block, False  # go back

        firsts = []
        for block in self.blocks:
            if len(block.jump_srcs) == 0:
                firsts.append(block)
        for block in firsts:
            visited = []
            for _ in _walk(block, visited, 0): yield _  # noqa

    def block_routes_to_terminals(self):
        routes = list()
        route = list()
        prev_foward = True
        # for block, gofoward in self.walk_blocks_all_routes_by_depth():
        for block, gofoward in self.walk_blocks_by_depth():
            if gofoward:
                route.append(block)
            else:
                if prev_foward:
                    routes.append(route[:])
                route.remove(block)
            prev_foward = gofoward
        return routes

    def walk_functions_by_depth(self):
        def _walk(func, visited):
            visited.append(func)
            yield func, True  # go foward
            for child in func.call_tgts:
                if child not in visited:
                    for _ in _walk(child, visited): yield _  # noqa
            yield func, False  # go back

        rest = [self]
        visited = []
        while len(rest) > 0:
            first = rest[0]
            for _ in _walk(first, visited): yield _  # noqa
            for f in visited:
                if f in rest:
                    rest.remove(f)


class DisassemblyObject():
    def __init__(self, elf, isa):
        self.elf = elf
        self.isa = isa
        self.blocks = list()
        self.functions = list()
        self._block_addrs = list()
        self._build_obj()

    def to_json(self):
        d = {
            'functions': [f.to_json() for f in self.functions],
            'blocks': [b.to_json() for b in self.blocks],
        }
        return d

    def _build_obj(self):
        print("# building object")
        print("## decoding")
        self.operators = self._decode()  # TODO: speed up
        text_sts = self._collect_text_symbol_tables()
        print("## collecting jumpt targets")
        block_addrs = [st.st_value for st in text_sts]
        block_addrs = sorted(list(set(block_addrs)))
        block_addrs += self._collect_jump_targets()
        print("## building basicblocks")
        block_addrs = sorted(list(set(block_addrs)))
        self._build_basicblocks(block_addrs, text_sts)  # TODO: speed up
        print("## building functions")
        self._build_functions(text_sts)
        print("# building cfg")
        self._build_control_flow_graph()
        print("# building dfg")
        self._build_data_flow_graph()

    def _text_section_headers(self):
        shs = list()
        for sh in self.elf.section_headers:
            is_progbits = (sh.sh_type == SectionHeader.SHT.index('PROGBITS'))
            is_executable = (sh.sh_flags & 6) == 6
            if is_progbits and is_executable:
                shs.append(sh)
        return shs

    def _text_section_header(self, obj):
        if isinstance(obj, SymbolTable):
            st = obj
            if st.st_shndx >= len(self.elf.shs) - 1:
                return None
            sh = self.elf.shs[st.st_shndx]
            if sh in self._text_section_headers():
                return sh
        elif isinstance(obj, int):
            addr = obj
            for sh in self._text_section_headers():
                if sh.sh_addr <= addr < sh.sh_addr + sh.sh_size:
                    return sh
        return None

    def _section_header(self, addr):
        for sh in self.elf.section_headers:
            if sh.sh_addr <= addr < sh.sh_addr + sh.sh_size:
                return sh
        return None

    def _decode(self):
        operators = list()
        for sh in self._text_section_headers():
            fidx = sh.sh_offset
            while fidx < sh.sh_offset + sh.sh_size:
                data = self.elf.f[fidx: fidx + 4]
                addr = sh.sh_addr + fidx - sh.sh_offset
                ins = self.isa.decode(data, addr=addr)
                op = Operator()
                op.ins = ins
                operators.append(op)
                fidx_old = fidx
                fidx += ins.bytesize
                if fidx == fidx_old:  # unknown ins.
                    fidx += 2  # isa.min_ins_bytesize
        return operators

    def _collect_text_symbol_tables(self):
        sts = list()
        for st in self.elf.symbol_tables:
            if self._text_section_header(st) is not None:
                sts.append(st)
        return sts

    def _collect_jump_targets(self):
        addrs = list()
        for op in self.operators:
            ins = op.ins
            is_jumps = any([ins.is_jump, ins.is_branch])
            is_calls = any([ins.is_call, ins.is_tail])
            if is_jumps:
                if not ins.is_indirect:
                    addrs.append(ins.target_addr())
                if op != self.operators[-1]:
                    addrs.append(op.addr + ins.bytesize)
            elif is_calls:
                if not ins.is_indirect:
                    addrs.append(ins.target_addr())
            elif ins.is_return:
                if op != self.operators[-1]:
                    addrs.append(op.addr + ins.bytesize)
        addrs = sorted(list(set(addrs)))
        return addrs

    def _build_basicblocks(self, addrs, text_sts):
        for i in range(len(addrs)):
            block = BasicBlock()
            block.disobj = self
            begin = addrs[i]
            end = addrs[i + 1] if i < len(addrs) - 1 else sys.maxsize
            sh = self._text_section_header(begin)
            if not sh:
                continue
            end = min(end, sh.sh_addr + sh.sh_size)
            block.addr = begin
            block.size = end - begin
            for st in text_sts:
                if st.st_value == begin:
                    block.symbols.append(st)
            self.blocks.append(block)
        op1000s = dict()
        for i, op in enumerate(self.operators):
            key = op.addr // 0x1000
            op1000s.setdefault(key, i)
        for block in self.blocks:
            opidx = op1000s.get(block.addr // 0x1000)
            op = self.operators[opidx]
            while block.addr > op.addr:
                opidx += 1
                if opidx >= len(self.operators):
                    break
                op = self.operators[opidx]
            op = self.operators[opidx]
            while block.addr <= op.addr and op.addr + op.size <= block.addr + block.size:
                block.operators.append(op)
                op.block = block
                opidx += 1
                if opidx >= len(self.operators):
                    break
                op = self.operators[opidx]
        for block in self.blocks:
            old_symbols = block.symbols[:]
            new_symbols = list()
            for st in old_symbols:
                if st.st_type == SymbolTable.STT.index('FUNC'):
                    new_symbols.append(st)
            for st in old_symbols:
                if st not in new_symbols:
                    new_symbols.append(st)
            block.symbols = new_symbols

    def _build_functions(self, text_sts):
        call_tgt_addrs = list()
        for op in self.operators:
            ins = op.ins
            is_calls = any([ins.is_call, ins.is_tail])
            if is_calls and not ins.is_indirect:
                call_tgt_addrs.append(ins.target_addr())
        call_tgt_addrs = list(set(call_tgt_addrs))
        func_symbols = dict()
        for st in text_sts:
            is_text = self._text_section_header(st) is not None
            is_func = st.st_type == SymbolTable.STT.index('FUNC')
            is_global = st.st_bind == SymbolTable.STB.index('GLOBAL')
            is_call_tgt = st.st_value in call_tgt_addrs
            if is_text and (is_func or is_global or is_call_tgt):
                addr = st.st_value
                func_symbols.setdefault(addr, list())
                func_symbols[addr].append(st)
        for block in self.blocks:
            sts = func_symbols.get(block.addr)
            if sts:
                func = Function()
                func.symbols = sts
                func.addr = block.addr
                func.size = sts[0].st_size
                self.functions.append(func)
        for fi, func in enumerate(self.functions):
            next_func = self.functions[fi + 1] if fi + 1 < len(self.functions) else None
            lastblock = self.blocks[-1]
            for block in self.blocks:
                if all([
                    func.addr <= block.addr,
                    block.addr + block.size <= func.addr + func.size
                ]):
                    func.blocks.append(block)
                    block.function = func
                elif next_func and all([
                    func.size == 0,
                    func.addr <= block.addr,
                    block.addr + block.size <= next_func.addr
                ]):
                    func.blocks.append(block)
                    block.function = func
                elif not next_func and all([
                    func.size == 0,
                    func.addr <= block.addr,
                    block.addr + block.size <= lastblock.addr + lastblock.size
                ]):
                    func.blocks.append(block)
                    block.function = func

    def _build_control_flow_graph(self):
        for op in self.operators:
            ins = op.ins
            is_branchs = any([ins.is_branch])
            is_jumps = any([ins.is_jump])
            is_calls = any([ins.is_call, ins.is_tail])
            if (is_jumps or is_branchs) and not ins.is_indirect:
                addr = ins.target_addr()
                for tgt_op in self.operators:
                    if tgt_op.addr == addr:
                        op.block.jump_tgts.append(tgt_op.block)
                        tgt_op.block.jump_srcs.append(op.block)
                        break
                if is_branchs:
                    addr = op.addr + ins.bytesize
                    for tgt_op in self.operators:
                        if tgt_op.addr == addr:
                            op.block.jump_tgts.append(tgt_op.block)
                            tgt_op.block.jump_srcs.append(op.block)
                            break
            elif is_calls and not ins.is_indirect:
                addr = ins.target_addr()
                for tgt_op in self.operators:
                    if tgt_op.addr == addr:
                        op.block.function.call_tgts.append(tgt_op.block.function)
                        tgt_op.block.function.call_srcs.append(op.block.function)
                        break
            elif ins.is_return:
                pass
            elif op == op.block.operators[-1]:
                addr = op.addr + ins.bytesize
                for tgt_op in self.operators:
                    if tgt_op.addr == addr:
                        op.block.jump_tgts.append(tgt_op.block)
                        tgt_op.block.jump_srcs.append(op.block)
                        break
        # separate cyclic jump srcs/tgts
        rests = self.blocks[:]
        while len(rests) > 0:
            blocks = [b for b, g in rests[0].walk_blocks_by_depth() if g]
            for block in blocks:
                if block in rests:
                    rests.remove(block)
                srcs = list()
                for b, gofoward in block.walk_blocks_by_depth():
                    if not gofoward:
                        continue
                    if block in b.jump_tgts:
                        srcs.append(b)
                for src in srcs:
                    block.jump_srcs.remove(src)
                    block.cyclic_jump_srcs.append(src)
                    src.jump_tgts.remove(block)
                    src.cyclic_jump_tgts.append(block)
        # compute rank of blocks
        for fi, func in enumerate(self.functions):
            # print("  {}/{} functions done.".format(fi + 1, len(self.functions)))
            rests = list()
            for block, gofoward in func.walk_blocks_by_depth():
                if not gofoward:
                    continue
                rests.append(block)
            for block in rests[:]:
                srcs = [b for b in block.jump_srcs_in_function]
                if len(srcs) == 0:
                    if block == func.blocks[0]:
                        block.rank = 0
                    else:
                        block.rank = 1
                    rests.remove(block)
            while len(rests) > 0:
                for block in rests[:]:
                    srcs = [b for b in block.jump_srcs_in_function]
                    if all([b.rank >= 0 for b in srcs]):
                        block.rank = max([b.rank for b in block.jump_srcs_in_function]) + 1
                        rests.remove(block)
        # separate outer jump srcs/tgts
        for block in self.blocks:
            tgts = list()
            for b in block.jump_tgts:
                if block.function and not b.isin(block.function):
                    tgts.append(b)
            for tgt in tgts:
                block.jump_tgts.remove(tgt)
                block.outer_jump_tgts.append(tgt)
                tgt.jump_srcs.remove(block)
                tgt.outer_jump_srcs.append(block)

    def _build_data_flow_graph(self):
        for func in self.functions:
            self.build_data_flow_graph(func)

    def build_data_flow_graph(self, func):
        # TODO: support loop structure for data flow graph
        def data_flow(operators):
            for di, dstop in enumerate(operators):
                for srcop in operators[di + 1:]:
                    if dstop.regs_used_in(srcop):
                        if dstop not in srcop.data_srcs:
                            srcop.data_srcs.append(dstop)
                        if srcop not in dstop.data_dsts:
                            dstop.data_dsts.append(srcop)
                    if dstop.regs_overwritten_by(srcop):
                        break
        for route in func.block_routes_to_terminals():
            ops = list()
            for block in route:
                ops += block.operators
            data_flow(ops)

    def walk_functions_by_depth(self):
        def _walk(func, visited):
            visited.append(func)
            yield func, True  # go foward
            for child in func.call_tgts:
                if child not in visited:
                    for _ in _walk(child, visited): yield _  # noqa
            yield func, False  # go back

        rest = self.functions[:]
        visited = []
        while len(rest) > 0:
            first = rest[0]
            for _ in _walk(first, visited): yield _  # noqa
            for f in visited:
                if f in rest:
                    rest.remove(f)
