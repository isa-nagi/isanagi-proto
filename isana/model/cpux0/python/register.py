from isana.isa import RegisterGroup, Register
from isana.isa import binary


class GPRReg(Register):
    pass


class SRReg(Register):
    bin = binary("$rsv[31:14], $I[0], $rsv[12:9], $M[2:0], $D[0], $rsv[4], $V[0], $C[0], $Z[0], $N[0]")


GPR_regs = (
    GPRReg(0, "r0", zero=True),
    GPRReg(1, "r1"),
    GPRReg(2, "r2"),
    GPRReg(3, "r3"),
    GPRReg(4, "r4"),
    GPRReg(5, "r5"),
    GPRReg(6, "r6"),
    GPRReg(7, "r7"),
    GPRReg(8, "r8"),
    GPRReg(9, "r9"),
    GPRReg(10, "r10"),
    GPRReg(11, "r11", gp=True),
    GPRReg(12, "r12", fp=True),
    GPRReg(13, "r13", sp=True),
    GPRReg(14, "r14", ra=True),
    GPRReg(15, "r15", status=True),
)

GPR = RegisterGroup("GPR", width=32, regs=(
    GPR_regs[:]
))

SR = RegisterGroup("SR", width=32, regs=(
    GPR_regs[15],
))

C0R = RegisterGroup("C0R", width=32, regs=(
    Register(0, "pc", dwarf_number=32),
    Register(1, "epc", dwarf_number=32),
))

SPR = RegisterGroup("SPR", width=32, regs=(
    Register(0, "ir", dwarf_number=32),
    Register(1, "mar", dwarf_number=32),
    Register(2, "mdr", dwarf_number=32),
    Register(3, "hi", dwarf_number=32),
    Register(4, "lo", dwarf_number=32),
))
