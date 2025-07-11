from isana.isa import binary
# from isana.isa import signed

# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrR, InstrR2,
    InstrIShift,
    # InstrS,
    # InstrB,
    # InstrU,
    # InstrJ,
    # InstrO,
)


class add_uw(InstrR):
    opn, opc = "add.uw", 0b0000100_00000_00000_000_00000_0111011


class sh1add(InstrR):
    opn, opc = "sh1add", 0b0010000_00000_00000_010_00000_0110011


class sh1add_uw(InstrR):
    opn, opc = "sh1add.uw", 0b0010000_00000_00000_010_00000_0111011


class sh2add(InstrR):
    opn, opc = "sh2add", 0b0010000_00000_00000_100_00000_0110011


class sh2add_uw(InstrR):
    opn, opc = "sh2add.uw", 0b0010000_00000_00000_100_00000_0111011


class sh3add(InstrR):
    opn, opc = "sh3add", 0b0010000_00000_00000_110_00000_0110011


class sh3add_uw(InstrR):
    opn, opc = "sh3add.uw", 0b0010000_00000_00000_110_00000_0111011


class slli_uw(InstrIShift):
    opn, opc = "slli.uw", 0b000010_000000_00000_001_00000_0011011
    bin = binary("$opc[31:26], $imm[5:0], $rs1[4:0], $opc[14:12], $rd[4:0], $opc[6:0]")


class zext_w(InstrR):
    opn, opc = "zext.w", 0b0000100_00000_00000_000_00000_0111011
    bin = binary("$opc[31:25], $rs2[4:0], $rs1[4:0], $opc[14:12], $opc[11:7], $opc[6:0]")


class andn(InstrR):
    opn, opc = "andn", 0b0100000_00000_00000_111_00000_0110011


class orn(InstrR):
    opn, opc = "orn", 0b0100000_00000_00000_110_00000_0110011


class xnor(InstrR):
    opn, opc = "xnor", 0b0100000_00000_00000_100_00000_0110011


class clz(InstrR2):
    opn, opc = "clz", 0b0110000_00000_00000_001_00000_0010011


class clzw(InstrR2):
    opn, opc = "clzw", 0b0110000_00000_00000_001_00000_0011011


class ctz(InstrR2):
    opn, opc = "ctz", 0b0110000_00001_00000_001_00000_0010011


class ctzw(InstrR2):
    opn, opc = "ctzw", 0b0110000_00001_00000_001_00000_0011011


class cpop(InstrR2):
    opn, opc = "cpop", 0b0110000_00010_00000_001_00000_0010011


class cpopw(InstrR2):
    opn, opc = "cpopw", 0b0110000_00010_00000_001_00000_0011011


class max_(InstrR):
    opn, opc = "max", 0b0000101_00000_00000_110_00000_0110011


class maxu(InstrR):
    opn, opc = "maxu", 0b0000101_00000_00000_111_00000_0110011


class min_(InstrR):
    opn, opc = "min", 0b0000101_00000_00000_100_00000_0110011


class minu(InstrR):
    opn, opc = "minu", 0b0000101_00000_00000_101_00000_0110011


class sext_b(InstrR2):
    opn, opc = "sext.b", 0b0110000_00100_00000_001_00000_0010011


class sext_h(InstrR2):
    opn, opc = "sext.b", 0b0110000_00101_00000_001_00000_0010011


class zext_h(InstrR2):
    opn, opc = "zext.h", 0b0000100_00000_00000_100_00000_0110011


class rol(InstrR):
    opn, opc = "rol", 0b0110000_00000_00000_001_00000_0110011


class rolw(InstrR):
    opn, opc = "rolw", 0b0110000_00000_00000_001_00000_0111011


class ror(InstrR):
    opn, opc = "ror", 0b0110000_00000_00000_101_00000_0110011


class rori(InstrIShift):
    opn, opc = "rori", 0b0110000_00000_00000_101_00000_0010011


class roriw(InstrIShift):
    opn, opc = "roriw", 0b0110000_00000_00000_101_00000_0011011


class rorw(InstrR):
    opn, opc = "rorw", 0b0110000_00000_00000_101_00000_0111011


class orc_b(InstrR2):
    opn, opc = "orc.b", 0b001010000111_00000_101_00000_0010011


class rev8(InstrR2):
    opn, opc = "rev8", 0b011010011000_00000_101_00000_0010011


class clmul(InstrR):
    opn, opc = "clmul", 0b0000101_00000_00000_001_00000_0110011


class clmulh(InstrR):
    opn, opc = "clmulh", 0b0000101_00000_00000_011_00000_0110011


class clmulr(InstrR):
    opn, opc = "clmulr", 0b0000101_00000_00000_010_00000_0110011


class bclr(InstrR):
    opn, opc = "bclr", 0b0100100_00000_00000_001_00000_0110011


class bclri(InstrIShift):
    opn, opc = "bclri", 0b0100100_00000_00000_001_00000_0010011


class bext(InstrR):
    opn, opc = "bext", 0b0100100_00000_00000_101_00000_0110011


class bexti(InstrIShift):
    opn, opc = "bexti", 0b0100100_00000_00000_101_00000_0010011


class binv(InstrR):
    opn, opc = "binv", 0b0110100_00000_00000_001_00000_0110011


class binvi(InstrIShift):
    opn, opc = "binvi", 0b0110100_00000_00000_001_00000_0010011


class bset(InstrR):
    opn, opc = "bset", 0b010100_00000_00000_001_00000_0110011


class bseti(InstrIShift):
    opn, opc = "bseti", 0b0010100_00000_00000_001_00000_0010011


instructionsZba = [
    sh1add,
    sh2add,
    sh3add,
]

instructionsZba64 = [
    add_uw,
    sh1add_uw,
    sh2add_uw,
    sh3add_uw,
    slli_uw,
    zext_w,
]

instructionsZbb = [
    andn,
    orn,
    xnor,
    clz,
    clzw,
    ctz,
    ctzw,
    cpop,
    cpopw,
    max_,
    maxu,
    min_,
    minu,
    sext_b,
    sext_h,
    zext_h,
    rol,
    rolw,
    ror,
    rori,
    roriw,
    rorw,
    orc_b,
    rev8,
]

instructionsZbc = [
    clmul,
    clmulh,
    clmulr,
]

instructionsZbs = [
    bclr,
    bclri,
    bext,
    bexti,
    binv,
    binvi,
    bset,
    bseti,
]
