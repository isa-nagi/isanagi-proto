from isana.isa import parameter  # , assembly, binary
# from isana.isa import signed

from .defs import xlen
# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrFR, InstrFR2, InstrFR4, InstrFRrm, InstrFR2rm,
    InstrFILoad,
    InstrFS,
)


class flw(InstrFILoad):
    opn, opc = "flw", 0b000000000000_00000_010_00000_0000111

    @property
    def is_load(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_pop(self):
        return self.params.inputs['rs1'].number == 2


class fsw(InstrFS):
    opn, opc = "fsw", 0b0000000_00000_00000_010_00000_0100111

    @property
    def is_store(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_push(self):
        return self.params.inputs['rs1'].number == 2


class fmadd_s(InstrFR4):
    opn, opc = "fmadd.s", 0b00000_00_00000_00000_000_00000_1000011


class fmsub_s(InstrFR4):
    opn, opc = "fmsub.s", 0b00000_00_00000_00000_000_00000_1000111


class fnmadd_s(InstrFR4):
    opn, opc = "fnmadd.s", 0b00000_00_00000_00000_000_00000_1001011


class fnmsub_s(InstrFR4):
    opn, opc = "fnmsub.s", 0b00000_00_00000_00000_000_00000_1001111


class fadd_s(InstrFRrm):
    opn, opc = "fadd.s", 0b0000000_00000_00000_000_00000_1010011


class fsub_s(InstrFRrm):
    opn, opc = "fsub.s", 0b0000100_00000_00000_000_00000_1010011


class fmul_s(InstrFRrm):
    opn, opc = "fmul.s", 0b0001000_00000_00000_000_00000_1010011


class fdiv_s(InstrFRrm):
    opn, opc = "fdiv.s", 0b0001100_00000_00000_000_00000_1010011


class fsqrt_s(InstrFR2rm):
    opn, opc = "fsqrt.s", 0b0101100_00000_00000_000_00000_1010011


class fsgnj_s(InstrFR):
    opn, opc = "fsgnj.s", 0b0010000_00000_00000_000_00000_1010011


class fsgnjn_s(InstrFR):
    opn, opc = "fsgnjn.s", 0b0010000_00000_00000_001_00000_1010011


class fsgnjx_s(InstrFR):
    opn, opc = "fsgnjx.s", 0b0010000_00000_00000_010_00000_1010011


class fmin_s(InstrFR):
    opn, opc = "fmin.s", 0b0010100_00000_00000_000_00000_1010011


class fmax_s(InstrFR):
    opn, opc = "fmin.s", 0b0010100_00000_00000_001_00000_1010011


class fcvt_w_s(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.w.s", 0b1100000_00000_00000_000_00000_1010011


class fcvt_wu_s(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.wu.s", 0b1100000_00001_00000_000_00000_1010011


class fmv_x_w(InstrFR2):
    prm = parameter("rd:GPR", "rs1:FPR")
    opn, opc = "fmv.x.w", 0b1110000_00000_00000_000_00000_1010011


class feq_s(InstrFR):
    opn, opc = "feq.s", 0b1010000_00000_00000_010_00000_1010011


class flt_s(InstrFR):
    opn, opc = "flt.s", 0b1010000_00000_00000_001_00000_1010011


class fle_s(InstrFR):
    opn, opc = "fle.s", 0b1010000_00000_00000_000_00000_1010011


class fclass_s(InstrFR):
    opn, opc = "fclass.s", 0b1110000_00000_00000_001_00000_1010011


class fcvt_s_w(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.s.w", 0b1101000_00000_00000_000_00000_1010011


class fcvt_s_wu(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.s.wu", 0b1101000_00001_00000_000_00000_1010011


class fmv_w_x(InstrFR2):
    prm = parameter("rd:FPR", "rs1:GPR")
    opn, opc = "fmv.w.x", 0b1111000_00000_00000_000_00000_1010011


class fcvt_l_s(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.l.s", 0b1100000_00010_00000_000_00000_1010011


class fcvt_lu_s(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.lu.s", 0b1100000_00011_00000_000_00000_1010011


class fcvt_s_l(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.s.l", 0b1101000_00010_00000_000_00000_1010011


class fcvt_s_lu(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.s.lu", 0b1101000_00011_00000_000_00000_1010011


# F
instructionsF = [
    flw,
    fsw,
    fmadd_s,
    fmsub_s,
    fnmadd_s,
    fnmsub_s,
    fadd_s,
    fsub_s,
    fmul_s,
    fdiv_s,
    fsqrt_s,
    fsgnj_s,
    fsgnjn_s,
    fsgnjx_s,
    fmin_s,
    fmax_s,
    fcvt_w_s,
    fcvt_wu_s,
    fmv_x_w,
    feq_s,
    flt_s,
    fle_s,
    fclass_s,
    fcvt_s_w,
    fcvt_s_wu,
    fmv_w_x,
]

if xlen == 64:
    instructionsF += [
        fcvt_l_s,
        fcvt_lu_s,
        fcvt_s_l,
        fcvt_s_lu,
    ]
