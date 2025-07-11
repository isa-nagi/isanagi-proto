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


class flh(InstrFILoad):
    opn, opc = "flh", 0b000000000000_00000_001_00000_0000111

    @property
    def is_load(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_pop(self):
        return self.params.inputs['rs1'].number == 2


class fsh(InstrFS):
    opn, opc = "fsh", 0b0000000_00000_00000_001_00000_0100111

    @property
    def is_store(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_push(self):
        return self.params.inputs['rs1'].number == 2


class fmadd_h(InstrFR4):
    opn, opc = "fmadd.h", 0b00000_10_00000_00000_000_00000_1000011


class fmsub_h(InstrFR4):
    opn, opc = "fmsub.h", 0b00000_10_00000_00000_000_00000_1000111


class fnmadd_h(InstrFR4):
    opn, opc = "fnmadd.h", 0b00000_10_00000_00000_000_00000_1001011


class fnmsub_h(InstrFR4):
    opn, opc = "fnmsub.h", 0b00000_10_00000_00000_000_00000_1001111


class fadd_h(InstrFRrm):
    opn, opc = "fadd.h", 0b0000010_00000_00000_000_00000_1010011


class fsub_h(InstrFRrm):
    opn, opc = "fsub.h", 0b0000110_00000_00000_000_00000_1010011


class fmul_h(InstrFRrm):
    opn, opc = "fmul.h", 0b0001010_00000_00000_000_00000_1010011


class fdiv_h(InstrFRrm):
    opn, opc = "fdiv.h", 0b0001110_00000_00000_000_00000_1010011


class fsqrt_h(InstrFR2rm):
    opn, opc = "fsqrt.h", 0b0101110_00000_00000_000_00000_1010011


class fsgnj_h(InstrFR):
    opn, opc = "fsgnj.h", 0b0010010_00000_00000_000_00000_1010011


class fsgnjn_h(InstrFR):
    opn, opc = "fsgnjn.h", 0b0010010_00000_00000_001_00000_1010011


class fsgnjx_h(InstrFR):
    opn, opc = "fsgnjx.h", 0b0010010_00000_00000_010_00000_1010011


class fmin_h(InstrFR):
    opn, opc = "fmin.h", 0b0010110_00000_00000_000_00000_1010011


class fmax_h(InstrFR):
    opn, opc = "fmin.h", 0b0010110_00000_00000_001_00000_1010011


class fcvt_s_h(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.s.h", 0b0100000_00010_00000_000_00000_1010011


class fcvt_h_s(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.h.s", 0b0100010_00000_00000_000_00000_1010011


class fcvt_d_h(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.d.h", 0b0100001_00010_00000_000_00000_1010011


class fcvt_h_d(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.h.d", 0b0100010_00001_00000_000_00000_1010011


class fcvt_q_h(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.q.h", 0b0100011_00010_00000_000_00000_1010011


class fcvt_h_q(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.h.q", 0b0100010_00011_00000_000_00000_1010011


class feq_h(InstrFR):
    opn, opc = "feq.h", 0b1010000_00000_00000_010_00000_1010011


class flt_h(InstrFR):
    opn, opc = "flt.h", 0b1010000_00000_00000_001_00000_1010011


class fle_h(InstrFR):
    opn, opc = "fle.h", 0b1010000_00000_00000_000_00000_1010011


class fclass_h(InstrFR):
    opn, opc = "fclass.h", 0b1110000_00000_00000_001_00000_1010011


class fcvt_w_h(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.w.h", 0b1100000_00000_00000_000_00000_1010011


class fcvt_wu_h(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.wu.h", 0b1100000_00001_00000_000_00000_1010011


class fmv_x_h(InstrFR2):
    prm = parameter("rd:GPR", "rs1:FPR")
    opn, opc = "fmv.x.h", 0b1110000_00000_00000_000_00000_1010011


class fcvt_h_w(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.h.w", 0b1101000_00000_00000_000_00000_1010011


class fcvt_h_wu(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.h.wu", 0b1101000_00001_00000_000_00000_1010011


class fmv_h_x(InstrFR2):
    prm = parameter("rd:FPR", "rs1:GPR")
    opn, opc = "fmv.h.x", 0b1111000_00000_00000_000_00000_1010011


class fcvt_l_h(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.l.h", 0b1100000_00010_00000_000_00000_1010011


class fcvt_lu_h(InstrFR2rm):
    prm = parameter("rd:GPR", "rs1:FPR, rm:Imm")
    opn, opc = "fcvt.lu.h", 0b1100000_00011_00000_000_00000_1010011


class fcvt_h_l(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.h.l", 0b1101000_00010_00000_000_00000_1010011


class fcvt_h_lu(InstrFR2rm):
    prm = parameter("rd:FPR", "rs1:GPR, rm:Imm")
    opn, opc = "fcvt.h.lu", 0b1101000_00011_00000_000_00000_1010011


# Zfh
instructionsZfh = [
    flh,
    fsh,
    fmadd_h,
    fmsub_h,
    fnmadd_h,
    fnmsub_h,
    fadd_h,
    fsub_h,
    fmul_h,
    fdiv_h,
    fsqrt_h,
    fsgnj_h,
    fsgnjn_h,
    fsgnjx_h,
    fmin_h,
    fmax_h,
    fcvt_s_h,
    fcvt_h_s,
    fcvt_d_h,
    fcvt_h_d,
    fcvt_q_h,
    fcvt_h_q,
    feq_h,
    flt_h,
    fle_h,
    fclass_h,
    fcvt_w_h,
    fcvt_wu_h,
    fmv_x_h,
    fcvt_h_w,
    fcvt_h_wu,
    fmv_h_x,
]

if xlen == 64:
    instructionsZfh += [
        fcvt_l_h,
        fcvt_lu_h,
        fcvt_h_l,
        fcvt_h_lu,
    ]
