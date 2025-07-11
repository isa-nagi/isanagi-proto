from isana.isa import parameter, assembly, binary
# from isana.isa import signed

from .defs import xlen
# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrCR, InstrCRJ, InstrCI01, InstrCI10, InstrCSS, InstrCIW, InstrCL, InstrCS,
    InstrCA, InstrCB, InstrCBBranch, InstrCJ, InstrCLB, InstrCSB, InstrCLH,
    InstrCSH, InstrCU, InstrCMMV, InstrCMJT, InstrCMPP,
)


class illegal(InstrCIW):
    opn, opc = "illegal", 0b000_00000000_000_00
    prm = parameter("", "")
    asm = assembly("$opn")
    bin = binary("$opc[15:0]")


class c_addi4spn(InstrCIW):
    opn, opc = "c.addi4spn", 0b000_00000000_000_00
    prm = parameter("rd:GPRC", "imm:ImmS32O2")
    bin = binary("$opc[15:13], $imm[5:4], $imm[9:6], $imm[2], $imm[3], $rd[2:0], $opc[1:0]")


class c_fld(InstrCL):
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:ImmS5O3")
    opn, opc = "c.fld", 0b001_000_000_00_000_00
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[7:6], $rd[2:0], $opc[1:0]")


class c_lq(InstrCL):
    opn, opc = "c.lq", 0b001_000_000_00_000_00
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:ImmS5O4")
    bin = binary("$opc[15:13], $imm[5:4], $imm[8], $rs1[2:0], $imm[7:6], $rd[2:0], $opc[1:0]")
    is_load = True


class c_lw(InstrCL):
    opn, opc = "c.lw", 0b010_000_000_00_000_00
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:ImmS5O2")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[2], $imm[6], $rd[2:0], $opc[1:0]")
    is_load = True


class c_flw(InstrCL):
    opn, opc = "c.flw", 0b011_000_000_00_000_00
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:ImmS5O2")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[2], $imm[6], $rd[2:0], $opc[1:0]")
    is_load = True


class c_ld(InstrCL):
    opn, opc = "c.ld", 0b011_000_000_00_000_00
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:ImmS5O3")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[7:6], $rd[2:0], $opc[1:0]")
    is_load = True


class c_fsd(InstrCS):
    opn, opc = "c.fsd", 0b101_000_000_00_000_00
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:ImmS5O3")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[7:6], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_sq(InstrCS):
    opn, opc = "c.sq", 0b101_000_000_00_000_00
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:ImmS5O4")
    bin = binary("$opc[15:13], $imm[5:4], $imm[8:8], $rs1[2:0], $imm[7:6], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_sw(InstrCS):
    opn, opc = "c.sw", 0b110_000_000_00_000_00
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:ImmS5O2")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[2], $imm[6], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_fsw(InstrCS):
    opn, opc = "c.fsw", 0b111_000_000_00_000_00
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:ImmS5O2")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[2], $imm[6], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_sd(InstrCS):
    opn, opc = "c.sd", 0b111_000_000_00_000_00
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:ImmS5O3")
    bin = binary("$opc[15:13], $imm[5:3], $rs1[2:0], $imm[7:6], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_nop(InstrCI01):
    opn, opc = "c.nop", 0b000_0_00000_00000_01
    bin = binary("$opc[15:13], $imm[5], $opc[11:7], $imm[4:0], $opc[1:0]")


class c_addi(InstrCI01):
    opn, opc = "c.addi", 0b000_0_00000_00000_01
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class c_jal(InstrCJ):
    opn, opc = "c.jal", 0b001_0_00000_00000_01
    prm = parameter("", "imm:ImmS11O1")
    bin = binary("$opc[15:13], $imm[11], $imm[4], $imm[9:8], $imm[10], "
                 "$imm[6], $imm[7], $imm[3:1], $imm[5], $opc[1:0]")
    is_call = True

    def semantic(self, ctx, ins):
        ctx.GPR[1] = ctx.PCR.pc + 4
        ctx.PCR.pc += ins.imm


class c_addiw(InstrCI01):
    opn, opc = "c.addiw", 0b001_0_00000_00000_01
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class c_li(InstrCI01):
    opn, opc = "c.li", 0b010_0_00000_00000_01
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class c_addi16sp(InstrCI01):
    opn, opc = "c.addi16sp", 0b011_0_00010_00000_01
    prm = parameter("rdrs1:GPR", "imm:ImmS6O4")
    asm = assembly("$opn $imm")
    bin = binary("$opc[15:13], $imm[9], $opc[11:7], $imm[4], $imm[6], $imm[8:7], $imm[5], $opc[1:0]")


class c_lui(InstrCI01):
    opn, opc = "c.lui", 0b011_0_00000_00000_01
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class c_srli(InstrCB):
    opn, opc = "c.srli", 0b100_0_00_000_00000_01
    bin = binary("$opc[15:13], $imm[5], $opc[11:10], $rdrs1[2:0], $imm[4:0], $opc[1:0]")


class c_srli64(InstrCB):
    opn, opc = "c.srli64", 0b100_0_00_000_00000_01
    bin = binary("$opc[15:13], $opc[12], $opc[11:10], $rdrs1[2:0], $opc[6:2], $opc[1:0]")


class c_srai(InstrCB):
    opn, opc = "c.srai", 0b100_0_01_000_00000_01
    bin = binary("$opc[15:13], $imm[5], $opc[11:10], $rdrs1[2:0], $imm[4:0], $opc[1:0]")


class c_srai64(InstrCB):
    opn, opc = "c.srai64", 0b100_0_01_000_00000_01
    bin = binary("$opc[15:13], $opc[12], $opc[11:10], $rdrs1[2:0], $opc[6:2], $opc[1:0]")


class c_andi(InstrCB):
    opn, opc = "c.srai", 0b100_0_10_000_00000_01
    bin = binary("$opc[15:13], $imm[5], $opc[11:10], $rdrs1[2:0], $imm[4:0], $opc[1:0]")


class c_sub(InstrCA):
    opn, opc = "c.sub", 0b100_0_11_000_00_000_01


class c_xor(InstrCA):
    opn, opc = "c.xor", 0b100_0_11_000_01_000_01


class c_or(InstrCA):
    opn, opc = "c.or", 0b100_0_11_000_10_000_01


class c_and(InstrCA):
    opn, opc = "c.and", 0b100_0_11_000_11_000_01


class c_subw(InstrCA):
    opn, opc = "c.subw", 0b100_1_11_000_00_000_01


class c_addw(InstrCA):
    opn, opc = "c.addw", 0b100_1_11_000_10_000_01


class c_j(InstrCJ):
    opn, opc = "c.j", 0b101_00000000000_01
    prm = parameter("", "imm:ImmS11O1")
    bin = binary("$opc[15:13], $imm[11], $imm[4], $imm[9:8], $imm[10], "
                 "$imm[6], $imm[7], $imm[3:1], $imm[5], $opc[1:0]")
    is_jump = True

    def semantic(self, ctx, ins):
        ctx.PCR.pc += ins.imm


class c_beqz(InstrCBBranch):
    opn, opc = "c.beqz", 0b110_000_000_00000_01
    prm = parameter("", "rdrs1:GPRC, imm:ImmS8O1")
    bin = binary("$opc[15:13], $imm[8], $imm[4:3], $rdrs1[2:0], "
                 "$imm[7:6], $imm[2:1], $imm[5], $opc[1:0]")
    is_branch = True

    def semantic(self, ctx, ins):
        cond = ctx.GPR[ins.rdrs1] == 0
        if cond:
            ctx.PCR.pc += ins.imm


class c_bnez(InstrCBBranch):
    opn, opc = "c.bnez", 0b111_000_000_00000_01
    prm = parameter("", "rdrs1:GPRC, imm:ImmS8O1")
    bin = binary("$opc[15:13], $imm[8], $imm[4:3], $rdrs1[2:0], "
                 "$imm[7:6], $imm[2:1], $imm[5], $opc[1:0]")
    is_branch = True

    def semantic(self, ctx, ins):
        cond = ctx.GPR[ins.rdrs1] != 0
        if cond:
            ctx.PCR.pc += ins.imm


class c_slli(InstrCI10):
    opn, opc = "c.slli", 0b000_0_00_000_00000_10
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class c_slli64(InstrCI10):
    opn, opc = "c.slli64", 0b000_0_00_000_00000_10
    bin = binary("$opc[15:13], $opc[12], $rdrs1[4:0], $opc[6:2], $opc[1:0]")


class c_fldsp(InstrCI10):
    opn, opc = "c.fldsp", 0b001_0_00_000_00000_10
    prm = parameter("rdrs1:GPR", "imm:ImmS6O3")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:3], $imm[8:6], $opc[1:0]")
    is_pop = True


class c_lqsp(InstrCI10):
    opn, opc = "c.lqsp", 0b001_0_00_000_00000_10
    prm = parameter("rdrs1:GPR", "imm:ImmS6O4")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4], $imm[9:6], $opc[1:0]")
    is_pop = True


class c_lwsp(InstrCI10):
    opn, opc = "c.lwsp", 0b010_0_00_000_00000_10
    prm = parameter("rdrs1:GPR", "imm:ImmS6O2")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:2], $imm[7:6], $opc[1:0]")
    is_pop = True


class c_flwsp(InstrCI10):
    opn, opc = "c.flwsp", 0b011_0_00_000_00000_10
    prm = parameter("rdrs1:GPR", "imm:ImmS6O2")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:2], $imm[7:6], $opc[1:0]")
    is_pop = True


class c_ldsp(InstrCI10):
    opn, opc = "c.ldsp", 0b011_0_00_000_00000_10
    prm = parameter("rdrs1:GPR", "imm:ImmS6O3")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:3], $imm[8:6], $opc[1:0]")
    is_pop = True


class c_jr(InstrCRJ):
    opn, opc = "c.jr", 0b1000_00000_00000_10
    is_indirect = True

    def semantic(self, ctx, ins):
        t = ctx.GPR[ins.rs1]
        ctx.PCR.pc = t + ins.imm

    @property
    def is_jump(self):
        return self.params.outputs['rdrs1'].number != 1

    @property
    def is_return(self):
        return self.params.outputs['rdrs1'].number == 1


class c_mv(InstrCR):
    opn, opc = "c.mv", 0b1000_00000_00000_10
    bin = binary("$opc[15:12], $rdrs1[4:0], $rs2[4:0], $opc[1:0]")


class c_ebreak(InstrCR):
    opn, opc = "c.ebreak", 0b1001_00000_00000_10
    bin = binary("$opc[15:0]")


class c_jalr(InstrCRJ):
    opn, opc = "c.jalr", 0b1001_00000_00000_10
    is_call = True
    is_indirect = True

    def semantic(self, ctx, ins):
        t = ctx.GPR[ins.rs1]
        ctx.GPR[1] = ctx.PCR.pc + 4
        ctx.PCR.pc = t


class c_add(InstrCR):
    opn, opc = "c.add", 0b1001_00000_00000_10
    bin = binary("$opc[15:12], $rdrs1[4:0], $rs2[4:0], $opc[1:0]")


class c_fsdsp(InstrCSS):
    opn, opc = "c.fsdsp", 0b101_000000_00000_10
    prm = parameter("", "rs2:GPR, imm:ImmS6O3")
    bin = binary("$opc[15:13], $imm[5:3], $imm[8:6], $rs2[4:0], $opc[1:0]")
    is_push = True


class c_sqsp(InstrCSS):
    opn, opc = "c.spsp", 0b101_000000_00000_10
    prm = parameter("", "rs2:GPR, imm:ImmS6O4")
    bin = binary("$opc[15:13], $imm[5:4], $imm[9:6], $rs2[4:0], $opc[1:0]")
    is_push = True


class c_swsp(InstrCSS):
    opn, opc = "c.swsp", 0b110_000000_00000_10
    prm = parameter("", "rs2:GPR, imm:ImmS6O2")
    bin = binary("$opc[15:13], $imm[5:2], $imm[7:6], $rs2[4:0], $opc[1:0]")
    is_push = True


class c_fswsp(InstrCSS):
    opn, opc = "c.fswsp", 0b111_000000_00000_10
    prm = parameter("", "rs2:GPR, imm:ImmS6O2")
    bin = binary("$opc[15:13], $imm[5:2], $imm[7:6], $rs2[4:0], $opc[1:0]")
    is_push = True


class c_sdsp(InstrCSS):
    opn, opc = "c.sdsp", 0b111_000000_00000_10
    prm = parameter("", "rs2:GPR, imm:ImmS6O3")
    bin = binary("$opc[15:13], $imm[5:3], $imm[8:6], $rs2[4:0], $opc[1:0]")
    is_push = True


class c_lbu(InstrCLB):
    opn, opc = "c.lbu", 0b100_000_000_00_000_00
    bin = binary("$opc[15:10], $rs1[2:0], $imm[0], $imm[1], $rd[2:0], $opc[1:0]")
    is_load = True


class c_lhu(InstrCLH):
    opn, opc = "c.lhu", 0b100_001_000_0_0_000_00
    bin = binary("$opc[15:10], $rs1[2:0], $opc[6], $imm[0], $rd[2:0], $opc[1:0]")
    is_load = True


class c_lh(InstrCLH):
    opn, opc = "c.lh", 0b100_001_000_1_0_000_00
    bin = binary("$opc[15:10], $rs1[2:0], $opc[6], $imm[0], $rd[2:0], $opc[1:0]")
    is_load = True


class c_sb(InstrCSB):
    opn, opc = "c.sb", 0b100_010_000_00_000_00
    bin = binary("$opc[15:10], $rs1[2:0], $imm[0], $imm[1], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_sh(InstrCSH):
    opn, opc = "c.sh", 0b100_011_000_00_000_00
    bin = binary("$opc[15:10], $rs1[2:0], $opc[6], $imm[0], $rs2[2:0], $opc[1:0]")
    is_store = True


class c_zext_b(InstrCU):
    opn, opc = "c.zext.b", 0b100_111_000_11_000_01


class c_sext_b(InstrCU):
    opn, opc = "c.sext.b", 0b100_111_000_11_001_01


class c_zext_h(InstrCU):
    opn, opc = "c.zext.h", 0b100_111_000_11_010_01


class c_sext_h(InstrCU):
    opn, opc = "c.sext.h", 0b100_111_000_11_011_01


class c_zext_w(InstrCU):
    opn, opc = "c.zext.w", 0b100_111_000_11_100_01


class c_not(InstrCU):
    opn, opc = "c.not", 0b100_111_000_11_101_01


class c_mul(InstrCA):
    opn, opc = "c.mul", 0b100_111_000_10_000_01


class cm_push(InstrCMPP):
    opn, opc = "cm.push", 0b101_11000_0000_00_10
    is_push = True


class cm_pop(InstrCMPP):
    opn, opc = "cm.pop", 0b101_11010_0000_00_10
    is_pop = True


class cm_popretz(InstrCMPP):
    opn, opc = "cm.popretz", 0b101_11100_0000_00_10
    is_pop = True


class cm_popret(InstrCMPP):
    opn, opc = "cm.popret", 0b101_11110_0000_00_10
    is_pop = True


class cm_mvsa01(InstrCMMV):
    opn, opc = "cm.mvsa01", 0b101_011_000_01_000_10


class cm_mva01s(InstrCMMV):
    opn, opc = "cm.mva01s", 0b101_011_000_11_000_10


class cm_jt(InstrCMJT):
    opn, opc = "cm.jt", 0b101_000_000_00000_10
    bin = binary("$opc[15:10], $opc[9:7], $imm[4:0], $opc[1:0]")
    # is_jump = True


class cm_jalt(InstrCMJT):
    opn, opc = "cm.jalt", 0b101_000_00000000_10
    # is_jump = True


instructionsZca = []

if xlen in (64, 128):
    instructionsZca += [
        c_ld,
        c_sd,
        c_addiw,
        c_subw,
        c_addw,
        c_ldsp,
        c_sdsp,
    ]

if xlen == 128:
    instructionsZca += [
        c_lq,
        c_sq,
        c_lqsp,
        c_sqsp,
    ]

instructionsZca += [
    illegal,
    c_addi4spn,
    c_lw,
    c_sw,
    c_nop,
    c_addi,
    c_jal,
    c_li,
    c_addi16sp,
    c_lui,
    c_srli,
    c_srli64,
    c_srai,
    c_srai64,
    c_andi,
    c_sub,
    c_xor,
    c_or,
    c_and,
    c_j,
    c_beqz,
    c_bnez,
    c_slli,
    c_slli64,
    c_lwsp,
    c_jr,
    c_mv,
    c_ebreak,
    c_jalr,
    c_add,
    c_swsp,
]

if xlen == 32:
    instructionsZcf = [
        c_flw,
        c_flwsp,
        c_fsw,
        c_fswsp,
    ]
else:
    instructionsZcf = []

instructionsZcd = [
    c_fld,
    c_fldsp,
    c_fsd,
    c_fsdsp,
]

# C = Zca [, Zcf, Zcd]
instructionsC = instructionsZca

instructionsZcb = [
    c_lbu,
    c_lhu,
    c_lh,
    c_sb,
    c_sh,
    c_zext_b,
    c_sext_b,
    c_zext_h,
    c_sext_h,
    c_zext_w,
    c_not,
    c_mul,
]

instructionsZcmp = [
    cm_push,
    cm_pop,
    cm_popret,
    cm_popretz,
    cm_mva01s,
    cm_mvsa01,
]

instructionsZcmt = [
    cm_jt,
    cm_jalt,
]
