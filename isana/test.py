import itertools
import random
import sys


def byteswap(value, bytesize):
    bs = value.to_bytes(bytesize)
    bs = reversed(bs)
    new_value = int.from_bytes(bs)
    return new_value


class TestBits():
    def __init__(self, msb, lsb, offset):
        self.msb = msb - lsb + offset
        self.lsb = lsb + offset

    def zero(self):
        '''zero'''
        return 0

    def one(self):
        '''one'''
        return 2 ** self.lsb

    def umax(self):
        '''umax'''
        v = 2 ** (self.msb + 1) - 1
        v -= 2 ** (self.lsb) - 1
        return v

    def smin(self):
        '''smin'''
        v = 2 ** (self.msb)
        return v

    def smax(self):
        '''smax'''
        v = 2 ** (self.msb) - 1
        v -= 2 ** (self.lsb) - 1
        return v

    def rand(self):
        '''rand'''
        v = random.randrange(self.one(), self.umax() + 1)
        return v


class TestOperand():
    def __init__(self, tp, param, isa):
        self.tp = tp
        self.param = param
        self.isa = isa

    def _get_reg_min_max(self, tp):
        group = None
        for group_ in self.isa.registers:
            if tp == group_.label:
                group = group_
                break
        else:
            return (None, None)
        min_ = sys.maxsize
        max_ = 0
        for reg in group.regs:
            min_ = min(min_, reg.idx)
            max_ = max(max_, reg.idx)
        return (min_, max_)

    def _get_imm_min_max(self, tp):
        imm = None
        for imm_ in self.isa.immediates:
            if tp == imm_.label:
                imm = imm_
                break
        else:
            return (None, None)
        if hasattr(imm, "signed"):
            min_ = imm.signed(2 ** (imm.width - 1))
            max_ = imm.signed(2 ** (imm.width - 1) - 1)
        else:
            min_ = 0
            max_ = 2 ** imm.width - 1
        return (min_, max_)

    def const(value):
        def _const(self):
            '''const'''
            param = self.param
            tp = self.tp
            if self.isa.is_opc_type(tp):
                pass
            elif self.isa.is_reg_type(tp):
                param.number = value
                param.value = None
            elif self.isa.is_imm_type(tp):
                param.number = None
                param.value = value
            return self.param
        return _const

    def zero(self):
        '''zero'''
        param = self.param
        tp = self.tp
        if self.isa.is_opc_type(tp):
            pass
        elif self.isa.is_reg_type(tp):
            param.number = 0
            param.value = None
        elif self.isa.is_imm_type(tp):
            param.number = None
            param.value = 0
        return self.param

    def one(self):
        '''one'''
        param = self.param
        tp = self.tp
        if self.isa.is_opc_type(tp):
            pass
        elif self.isa.is_reg_type(tp):
            param.number = 1
            param.value = None
        elif self.isa.is_imm_type(tp):
            param.number = None
            param.value = 1
        return self.param

    def min(self):
        '''min'''
        param = self.param
        tp = self.tp
        if self.isa.is_opc_type(tp):
            pass
        elif self.isa.is_reg_type(tp):
            min_, max_ = self._get_reg_min_max(tp)
            param.number = min_
        elif self.isa.is_imm_type(tp):
            min_, max_ = self._get_imm_min_max(tp)
            param.number = None
            param.value = min_
        return self.param

    def max(self):
        '''max'''
        param = self.param
        tp = self.tp
        if self.isa.is_opc_type(tp):
            pass
        elif self.isa.is_reg_type(tp):
            min_, max_ = self._get_reg_min_max(tp)
            param.number = max_
            param.value = None
        elif self.isa.is_imm_type(tp):
            min_, max_ = self._get_imm_min_max(tp)
            param.number = None
            param.value = max_
        return self.param

    def rand(self):
        '''rand'''
        param = self.param
        tp = self.tp
        if self.isa.is_opc_type(tp):
            pass
        elif self.isa.is_reg_type(tp):
            min_, max_ = self._get_reg_min_max(tp)
            param.number = random.randrange(min_, max_ + 1)
            param.value = None
        elif self.isa.is_imm_type(tp):
            min_, max_ = self._get_imm_min_max(tp)
            param.number = None
            param.value = random.randrange(min_, max_ + 1)
        return self.param


class InstructionTest():
    def __init__(self, isa, instr):
        self.isa = isa
        self.instr = instr()
        self.instr.isa = self.isa
        self.reg_alias = True

    def merge_case(self, cases):
        _cases = [list(r.items()) for r in cases]
        _cases = [(r[0], (r[1][0], [r[1][1]])) for r in _cases]
        new_cases = [_cases[0]]
        for r in _cases[1:]:
            keys = tuple(nr[0][1] for nr in new_cases)
            try:
                idx = keys.index(r[0][1])
                new_cases[idx][1][1].append(r[1][1])
            except Exception:
                new_cases.append(r)
        _cases = [dict(r) for r in new_cases]
        return _cases

    def gen_binary_edge_case(self):
        len_bits_ex_opc = len([b for b in self.instr.bin.bitss if b.label != "$opc"])
        valuefuncs = [
            TestBits.zero,
            TestBits.one,
            TestBits.smin,
            TestBits.smax,
            TestBits.umax,
        ]
        valuefuncs = list(itertools.product(valuefuncs, repeat=len_bits_ex_opc))
        cases = self.gen_binary_case(valuefuncs)
        return cases

    def gen_binary_random_case(self, repeat=1):
        len_bits_ex_opc = len([b for b in self.instr.bin.bitss if b.label != "$opc"])
        valuefuncs = [[TestBits.rand] * len_bits_ex_opc] * repeat
        cases = self.gen_binary_case(valuefuncs)
        return cases

    def gen_binary_case(self, valuefuncs):
        offsets = []
        sum_bits = 0
        for bits in reversed(self.instr.bin.bitss):
            offsets.append(sum_bits)
            sum_bits += bits.msb - bits.lsb + 1
        offsets.reverse()

        cases = []
        for vfi in range(len(valuefuncs)):
            value = 0
            funcstrs = []
            bi_ex_opc = 0
            for bi, bits in enumerate(self.instr.bin.bitss):
                msb = bits.msb + offsets[bi]
                lsb = bits.lsb + offsets[bi]
                tbits = TestBits(bits.msb, bits.lsb, offsets[bi])
                if bits.label == "$opc":
                    tvalue = self.instr.opc
                    tvalue &= ((2 ** (msb + 1) - 1) - (2 ** lsb - 1))
                    funcstr = bits.label
                else:
                    funcstr = "{}:{}".format(
                        bits.label,
                        valuefuncs[vfi][bi_ex_opc].__name__,
                    )
                    tvalue = valuefuncs[vfi][bi_ex_opc](tbits)
                value += tvalue
                funcstrs.append(funcstr)
                if bits.label != "$opc":
                    bi_ex_opc += 1
            if self.isa.endian == "big":
                value = byteswap(value, self.instr.bytesize)
            cases.append({'value': value, 'func': funcstrs})
        return cases

    def gen_asm_edge_case(self):
        len_ops_ex_opc = 0
        for ast in self.instr.asm.ast:
            if ast[0] == "$" and ast != "$opn":
                len_ops_ex_opc += 1
        valuefuncs = [
            TestOperand.zero,
            TestOperand.one,
            TestOperand.min,
            TestOperand.max,
        ]
        valuefuncs = list(itertools.product(valuefuncs, repeat=len_ops_ex_opc))
        cases = self.gen_asm_case(valuefuncs)
        return cases

    def gen_asm_random_case(self, repeat=1):
        len_ops_ex_opc = 0
        for ast in self.instr.asm.ast:
            if ast[0] == "$" and ast != "$opn":
                len_ops_ex_opc += 1
        valuefuncs = [[TestOperand.rand] * len_ops_ex_opc] * repeat
        cases = self.gen_asm_case(valuefuncs)
        return cases

    def gen_asm_case(self, valuefuncs):
        cases = []
        for vfi in range(len(valuefuncs)):
            self.instr.decode(self.instr.opc)
            asm = ""
            funcstrs = []
            opi_ex_opc = 0
            for ast in self.instr.asm.ast:
                if ast == "$opn":
                    asm += self.instr.opn
                elif ast[0] == "$":
                    label = ast[1:]
                    if label in self.instr.prm.outputs:
                        tp = self.instr.prm.outputs[label]
                        param = self.instr.params.outputs[label]
                        top = TestOperand(tp, param, self.isa)
                        tparam = valuefuncs[vfi][opi_ex_opc](top)
                        asm += self.isa.param_str(tparam, alias=self.reg_alias)
                    elif label in self.instr.params.inputs:
                        tp = self.instr.prm.inputs[label]
                        param = self.instr.params.inputs[label]
                        top = TestOperand(tp, param, self.isa)
                        tparam = valuefuncs[vfi][opi_ex_opc](top)
                        asm += self.isa.param_str(tparam, alias=self.reg_alias)
                    else:
                        asm += "#" + ast
                    funcstr = "{}:{}".format(
                        ast,
                        # valuefuncs[vfi][opi_ex_opc].__name__,
                        valuefuncs[vfi][opi_ex_opc].__doc__,
                    )
                    opi_ex_opc += 1
                    funcstrs.append(funcstr)
                else:
                    asm += ast
            cases.append({'asm': asm, 'func': funcstrs})
        return cases
