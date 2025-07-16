from isana.isa import Instruction
from isana.isa import parameter, assembly, binary
# from isana.isa import signed
# from isana.isa import unimpl

# from .memory import Mem
# from .register import GPR, GPRC, VPR, CSR, PCR


class Instr32(Instruction):
    bin = binary("$opc[31:0]")


class Instr16_00(Instruction):
    bin = binary("$opc[15:0]")


class Instr16_01(Instruction):
    bin = binary("$opc[15:0]")


class Instr16_10(Instruction):
    bin = binary("$opc[15:0]")


# Type for Base Instruction Set
class InstrR(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, rs2:GPR")
    asm = assembly("$opn $rd, $rs1, $rs2")
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrR2(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR")
    asm = assembly("$opn $rd, $rs1")
    bin = binary("$opc[31:25], $opc[24:20], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrIJalr(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rd, $rs1, $imm")
    bin = binary("$imm[11:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrIAlu(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rd, $rs1, $imm")
    bin = binary("$imm[11:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrIFencei(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rd, $rs1, $imm")
    bin = binary("$imm[11:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrIShift(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:Imm")
    asm = assembly("$opn $rd, $rs1, $imm")
    bin = binary("$opc[31:25], $imm[4:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrIShift64(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:Imm")
    asm = assembly("$opn $rd, $rs1, $imm")
    bin = binary("$opc[31:26], $imm[5:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrILoad(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rd, $imm ($rs1)")
    bin = binary("$imm[11:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrIFence(Instr32):
    prm = parameter("", "pred:ImmU4, succ:ImmU4")
    asm = assembly("$opn $pred, $succ")
    bin = binary("$opc[31:28], $pred[3:0], $succ[3:0], $opc[19:0]")


class InstrS(Instr32):
    prm = parameter("", "rs2:GPR, rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rs2, $imm ($rs1)")
    bin = binary("$imm[11:5], $rs2[4:0], $rs1[4:0], $opc[14:12], $imm[4:0], $opc[6:0]")


class InstrB(Instr32):
    prm = parameter("", "rs1:GPR, rs2:GPR, imm:ImmS12O1")
    asm = assembly("$opn $rs1, $rs2, $imm")
    bin = binary("$imm[12], $imm[10:5], $rs2[4:0], $rs1[4:0], $opc[14:12], $imm[4:1], $imm[11], $opc[6:0]")


class InstrU(Instr32):
    prm = parameter("rd:GPR", "imm:ImmS20O12")
    asm = assembly("$opn $rd, $imm")
    bin = binary("$imm[31:12], $rd[4:0], $opc[6:0]")


class InstrJ(Instr32):
    prm = parameter("rd:GPR", "imm:ImmS20O1")
    asm = assembly("$opn $rd, $imm")
    bin = binary("$imm[20], $imm[10:1], $imm[11], $imm[19:12], $rd[4:0], $opc[6:0]")


class InstrO(Instr32):
    prm = parameter("", "")
    asm = assembly("$opn")
    bin = binary("$opc[31:0]")


class InstrCSRR(Instr32):
    prm = parameter("rd:GPR, csr:CSR", "csr:CSR, rs1:GPR")
    asm = assembly("$opn $rd, $csr, $rs1")
    bin = binary("$csr[11:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrCSRI(Instr32):
    prm = parameter("rd:GPR, csr:CSR", "csr:CSR, imm:Imm")
    asm = assembly("$opn $rd, $csr, $imm")
    bin = binary("$csr[11:0], $imm[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


# Type for C-extention
class InstrCR(Instr16_10):
    prm = parameter("rdrs1:GPR", "rs2:GPR")
    asm = assembly("$opn $rdrs1, $rs2")
    bin = binary("$opc[15:12], $rdrs1[4:0], $rs2[4:0], $opc[1:0]")

class InstrCRJ(Instr16_10):
    prm = parameter("", "rs1:GPR")
    asm = assembly("$opn $rs1")
    bin = binary("$opc[15:12], $rs1[4:0], $opc[6:2], $opc[1:0]")

class InstrCREbreak(Instr16_10):
    prm = parameter("", "")
    asm = assembly("$opn")
    bin = binary("$opc[15:12], $opc[11:7], $opc[6:2], $opc[1:0]")


class InstrCI01(Instr16_01):
    prm = parameter("rdrs1:GPR", "imm:ImmS6")
    asm = assembly("$opn $rdrs1, $imm")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class InstrCI01Nop(Instr16_01):
    prm = parameter("", "")
    asm = assembly("$opn")
    bin = binary("$opc[15:13], $opc[12], $opc[11:7], $opc[6:2], $opc[1:0]")


class InstrCI10(Instr16_10):
    prm = parameter("rdrs1:GPR", "imm:ImmS6")
    asm = assembly("$opn $rdrs1, $imm")
    bin = binary("$opc[15:13], $imm[5], $rdrs1[4:0], $imm[4:0], $opc[1:0]")


class InstrCSS(Instr16_10):
    prm = parameter("", "rs2:GPR, imm:ImmS6")
    asm = assembly("$opn $rs2, $imm")
    bin = binary("$opc[15:13], $imm[5:0], $rs2[4:0], $opc[1:0]")


class InstrCIW(Instr16_00):
    prm = parameter("rd:GPRC", "imm:Imm")
    asm = assembly("$opn $rd, $imm")
    bin = binary("$opc[15:13], $imm[7:0], $rd[2:0], $opc[1:0]")


class InstrCL(Instr16_00):
    prm = parameter("rd:GPRC", "rs1:GPRC, imm:Imm")
    asm = assembly("$opn $rd, $imm ($rs1)")
    bin = binary("$opc[15:13], $imm[4:2], $rs1[2:0], $imm[1:0], $rd[2:0], $opc[1:0]")


class InstrCS(Instr16_00):
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:Imm")
    asm = assembly("$opn $rs2, $imm ($rs1)")
    bin = binary("$opc[15:13], $imm[4:2], $rs1[2:0], $imm[1:0], $rs2[2:0], $opc[1:0]")


class InstrCA(Instr16_01):
    prm = parameter("rdrs1:GPRC", "rdrs1:GPRC, rs2:GPRC")
    asm = assembly("$opn $rdrs1, $rs2")
    bin = binary("$opc[15:10], $rdrs1[2:0], $opc[6:5], $rs2[2:0], $opc[1:0]")


class InstrCB(Instr16_01):
    prm = parameter("rdrs1:GPRC", "rdrs1:GPRC, imm:ImmS9")
    asm = assembly("$opn $rdrs1, $imm")
    bin = binary("$opc[15:13], $imm[7:5], $rdrs1[2:0], $imm[4:0], $opc[1:0]")


class InstrCBBranch(Instr16_01):
    prm = parameter("", "rdrs1:GPRC, imm:ImmS9")
    asm = assembly("$opn $rdrs1, $imm")
    bin = binary("$opc[15:13], $imm[7:5], $rdrs1[2:0], $imm[4:0], $opc[1:0]")


class InstrCJ(Instr16_01):
    prm = parameter("", "imm:ImmS12")
    asm = assembly("$opn $imm")
    bin = binary("$opc[15:13], $imm[10:0], $opc[1:0]")


class InstrCLB(Instr16_00):
    prm = parameter("rd:GPRC", "rd:GPRC, rs1:GPRC, imm:Imm")
    asm = assembly("$opn $rd, $imm ($rs1)")
    bin = binary("$opc[15:10], $rs1[2:0], $imm[1:0], $rd[2:0], $opc[1:0]")


class InstrCSB(Instr16_00):
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:Imm")
    asm = assembly("$opn $rs2, $imm ($rs1)")
    bin = binary("$opc[15:10], $rs1[2:0], $imm[1:0], $rs2[2:0], $opc[1:0]")


class InstrCLH(Instr16_00):
    prm = parameter("rd:GPRC", "rd:GPRC, rs1:GPRC, imm:Imm")
    asm = assembly("$opn $rd, $imm ($rs1)")
    bin = binary("$opc[15:10], $rs1[2:0], $opc[6], $imm[0], $rd[2:0], $opc[1:0]")


class InstrCSH(Instr16_00):
    prm = parameter("", "rs2:GPRC, rs1:GPRC, imm:Imm")
    asm = assembly("$opn $rs2, $imm ($rs1)")
    bin = binary("$opc[15:10], $rs1[2:0], $opc[6], $imm[0], $rs2[2:0], $opc[1:0]")


class InstrCU(Instr16_01):
    prm = parameter("rdrs1:GPRC", "rdrs1:GPRC")
    asm = assembly("$opn $rdrs1")
    bin = binary("$opc[15:10], $rdrs1[2:0], $opc[6:2], $opc[1:0]")


class InstrCMMV(Instr16_10):
    prm = parameter("", "rs1:GPRC, rs2:GPRC")
    asm = assembly("$opn $rs1, $rs2")
    bin = binary("$opc[15:10], $rs1[2:0], $opc[6:5], $rs2[2:0], $opc[1:0]")


class InstrCMJT(Instr16_10):
    prm = parameter("", "imm:Imm")
    asm = assembly("$opn $imm")
    bin = binary("$opc[15:10], $imm[7:0], $opc[1:0]")


class InstrCMPP(Instr16_10):
    prm = parameter("", "rlist:Imm, imm:ImmS2O4")
    asm = assembly("$opn $rlist, $imm")
    bin = binary("$opc[15:10], $opc[9:8], $rlist[3:0], $imm[5:4], $opc[1:0]")


# Type for F-extention
class InstrFR(Instr32):
    prm = parameter("rd:FPR", "rs1:FPR, rs2:FPR")
    asm = assembly("$opn $rd, $rs1, $rs2")
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrFR2(Instr32):
    prm = parameter("rd:FPR", "rs1:FPR")
    asm = assembly("$opn $rd, $rs1")
    bin = binary("$opc[31:25], $opc[24:20], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrFR4(Instr32):
    prm = parameter("rd:FPR", "rs1:FPR, rs2:FPR, rs3:FPR, rm:RMImm")
    asm = assembly("$opn $rd, $rs1, $rs2, $rs3, $rm")
    bin = binary("$rs3[4:0], $opc[26:25], $rs2[4:0], $rs1[4:0], $rm[2:0], $rd[4:0], $opc[6:0]")


class InstrFRrm(Instr32):
    prm = parameter("rd:FPR", "rs1:FPR, rs2:FPR, rm:RMImm")
    asm = assembly("$opn $rd, $rs1, $rs2, $rm")
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $rm[2:0], $rd[4:0], $opc[6:0]")


class InstrFR2rm(Instr32):
    prm = parameter("rd:FPR", "rs1:FPR, rm:RMImm")
    asm = assembly("$opn $rd, $rs1, $rm")
    bin = binary("$opc[31:25], $opc[24:20], $rs1[4:0], $rm[2:0], $rd[4:0], $opc[6:0]")


class InstrFILoad(Instr32):
    prm = parameter("rd:FPR", "rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rd, $imm ($rs1)")
    bin = binary("$imm[11:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrFS(Instr32):
    prm = parameter("rs2:FPR", "rs1:GPR, imm:ImmS12")
    asm = assembly("$opn $rs2, $imm ($rs1)")
    bin = binary("$imm[11:5], $rs2[4:0], $rs1[4:0], $opc[14:12], $imm[4:0], $opc[6:0]")


# Type for V-extention
class InstrVLoadFP0(Instr32):
    prm = parameter("vd:VPR", "rs1:GPR, vm:Imm")
    asm = assembly("$opn $rd, $rs1")
    bin = binary("$opc[31:25], $opc[24:20], $rs1[4:0], $opc[14:12], $vd[4:0], $opc[6:0]")


class InstrVLoadFP1(Instr32):
    prm = parameter("vd:VPR", "rs1:GPR, rs2:GPR, vm:Imm")
    asm = assembly("$opn $vd, $rs1, $rs2")
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $opc[14:12], $vd[4:0], $opc[6:0]")


class InstrVLoadFP2(Instr32):
    prm = parameter("vd:VPR", "rs1:GPR, vs2:VPR, vm:Imm")
    asm = assembly("$opn $vd, $rs1, $vs2")
    bin = binary("$opc[31:25], $vs2[4:0], $rs1[4:0], $opc[14:12], $vd[4:0], $opc[6:0]")


class InstrVStoreFP0(Instr32):
    prm = parameter("vs3:VPR", "rs1:GPR, vm:Imm")
    asm = assembly("$opn $rs1, $vs3")
    bin = binary("$opc[31:25], $opc[24:20], $rs1[4:0], $opc[14:12], $vs3[4:0], $opc[6:0]")


class InstrVStoreFP1(Instr32):
    prm = parameter("vs3:VPR", "rs1:GPR, rs2:GPR, vm:Imm")
    asm = assembly("$opn $rs1, $rs2, $vs3")
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $opc[14:12], $vs3[4:0], $opc[6:0]")


class InstrVStoreFP2(Instr32):
    prm = parameter("vs3:VPR", "rs1:GPR, vs2:VPR, vm:Imm")
    asm = assembly("$opn $rs1, $vs2, $vs3")
    bin = binary("$opc[31:25], $vs2[4:0], $rs1[4:0], $opc[14:12], $vs3[4:0], $opc[6:0]")


class InstrVArith0(Instr32):
    prm = parameter("vd:VPR", "vs1:VPR, vs2:VPR, vm:Imm")
    asm = assembly("$opn $vd, $vs1, $vs2")
    bin = binary("$opc[31:25], $vs2[4:0], $rs1[4:0], $opc[14:12], $vd[4:0], $opc[6:0]")


class InstrVArith12(Instr32):
    prm = parameter("vdrd:VGPR", "vs1:VPR, vs2:VPR, vm:Imm")
    asm = assembly("$opn $vdrd, $vs1, $vs2")
    bin = binary("$opc[31:25], $vs2[4:0], $vs1[4:0], $opc[14:12], $vdrd[4:0], $opc[6:0]")


class InstrVArith3(Instr32):
    prm = parameter("vd:VPR", "imm:Imm, vs2:VPR, vm:Imm")
    asm = assembly("$opn $vd, $imm, $vs2")
    bin = binary("$opc[31:25], $vs2[4:0], $imm[4:0], $opc[14:12], $vd[4:0], $opc[6:0]")


class InstrVArith45(Instr32):
    prm = parameter("vd:VPR", "rs1:VPR, vs2:VPR, vm:Imm")
    asm = assembly("$opn $vd, $rs1, $vs2")
    bin = binary("$opc[31:25], $vs2[4:0], $rs1[4:0], $opc[14:12], $vd[4:0], $opc[6:0]")


class InstrVArith6(Instr32):
    prm = parameter("vdrd:VGPR", "rs1:VPR, vs2:VPR, vm:Imm")
    asm = assembly("$opn $vdrd, $rs1, $vs2")
    bin = binary("$opc[31:25], $vs2[4:0], $rs1[4:0], $opc[14:12], $vdrd[4:0], $opc[6:0]")


class InstrVConf0(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, vtypei:Imm")
    asm = assembly("$opn $rd, $rs1, $vtypei")
    bin = binary("$opc[31], $vtypei[10:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrVConf1(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, imm:Imm, vtypei:Imm")
    asm = assembly("$opn $rd, $rs1, $imm, $vtypei")
    bin = binary("$opc[31:25], $vtypei[9:0], $imm[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class InstrVConf2(Instr32):
    prm = parameter("rd:GPR", "rs1:GPR, rs2:GPR")
    asm = assembly("$opn $rd, $rs1, $rs2")
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")
