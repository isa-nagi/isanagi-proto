from isana.isa import ImmS, ImmU
from .defs import xlen


class ImmSXlen(ImmS):
    base = f"i{xlen}"


class ImmUXlen(ImmU):
    base = f"u{xlen}"


Imm = ImmSXlen("Imm", width=32)
ImmS12 = ImmSXlen("ImmS12", width=12)
ImmS12O1 = ImmSXlen("ImmS12O1", width=12, offset=1)
ImmS20O1 = ImmSXlen("ImmS20O1", width=20, offset=1)
ImmS20O12 = ImmSXlen("ImmS20O12", width=20, offset=12)
ImmS6 = ImmSXlen("ImmS6", width=6)
ImmS9 = ImmSXlen("ImmS9", width=9)
ImmS32O2 = ImmSXlen("ImmS32O2", width=32, offset=2)
ImmS5O2 = ImmSXlen("ImmS5O2", width=5, offset=2)
ImmS5O3 = ImmSXlen("ImmS5O3", width=5, offset=3)
ImmS5O4 = ImmSXlen("ImmS5O4", width=5, offset=4)
ImmS11O1 = ImmSXlen("ImmS11O1", width=11, offset=1)
ImmS6O2 = ImmSXlen("ImmS6O2", width=6, offset=2)
ImmS6O3 = ImmSXlen("ImmS6O3", width=6, offset=3)
ImmS6O4 = ImmSXlen("ImmS6O4", width=6, offset=4)
ImmS8O1 = ImmSXlen("ImmS8O1", width=8, offset=1)
ImmS2O4 = ImmSXlen("ImmS2O4", width=2, offset=4)
ImmU4 = ImmUXlen("ImmU4", width=4)
RMImm = ImmUXlen("RMImm", width=3, enums={
    0: "rne",
    1: "rtz",
    2: "rdn",
    3: "rup",
    4: "rmm",
    7: "dyn",
})
