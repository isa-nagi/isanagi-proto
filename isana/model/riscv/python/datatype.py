from isana.isa import Immediate, ImmS, ImmU

Imm = Immediate("Imm", width=32)
ImmS12 = ImmS("ImmS12", width=12)
ImmS12O1 = ImmS("ImmS12O1", width=12, offset=1)
ImmS20O1 = ImmS("ImmS20O1", width=20, offset=1)
ImmS20O12 = Immediate("ImmS20O12", width=20, offset=12)
ImmS6 = ImmS("ImmS6", width=6)
ImmS9 = ImmS("ImmS9", width=9)
ImmS32O2 = Immediate("ImmS32O2", width=32, offset=2)
ImmS5O2 = Immediate("ImmS5O2", width=5, offset=2)
ImmS5O3 = Immediate("ImmS5O3", width=5, offset=3)
ImmS5O4 = Immediate("ImmS5O4", width=5, offset=4)
ImmS11O1 = ImmS("ImmS11O1", width=11, offset=1)
ImmS6O2 = Immediate("ImmS6O2", width=6, offset=2)
ImmS6O3 = Immediate("ImmS6O3", width=6, offset=3)
ImmS6O4 = Immediate("ImmS6O4", width=6, offset=4)
ImmS8O1 = ImmS("ImmS8O1", width=8, offset=1)
ImmS2O4 = ImmS("ImmS2O4", width=2, offset=4)
ImmU4 = ImmU("ImmU4", width=4)
RMImm = Immediate("RMImm", width=3, enums={
    0: "rne",
    1: "rtz",
    2: "rdn",
    3: "rup",
    4: "rmm",
    7: "dyn",
})
