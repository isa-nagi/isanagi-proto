# from isana.isa import parameter, assembly, binary
# from isana.isa import signed

from .defs import xlen
# from .memory import Mem
# from .register import GPR, GPRC, CSR, PCR
from .instructionType import (
    InstrR,
)


class lr_w(InstrR):
    opn, opc = "lr.w", 0b00010_0_0_00000_00000_010_00000_0101111

    @property
    def is_load(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_pop(self):
        return self.params.inputs['rs1'].number == 2


class sc_w(InstrR):
    opn, opc = "sc.w", 0b00011_0_0_00000_00000_010_00000_0101111

    @property
    def is_store(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_push(self):
        return self.params.inputs['rs1'].number == 2


class InstrAMO(InstrR):
    @property
    def is_load(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_pop(self):
        return self.params.inputs['rs1'].number == 2

    @property
    def is_store(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_push(self):
        return self.params.inputs['rs1'].number == 2


class amoswap_w(InstrAMO):
    opn, opc = "amoswap.w", 0b00001_0_0_00000_00000_010_00000_0101111


class amoadd_w(InstrAMO):
    opn, opc = "amoadd.w", 0b00000_0_0_00000_00000_010_00000_0101111


class amoxor_w(InstrAMO):
    opn, opc = "amoxor.w", 0b00100_0_0_00000_00000_010_00000_0101111


class amoand_w(InstrAMO):
    opn, opc = "amoand.w", 0b01100_0_0_00000_00000_010_00000_0101111


class amoor_w(InstrAMO):
    opn, opc = "amoor.w", 0b01000_0_0_00000_00000_010_00000_0101111


class amomin_w(InstrAMO):
    opn, opc = "amomin.w", 0b10000_0_0_00000_00000_010_00000_0101111


class amomax_w(InstrAMO):
    opn, opc = "amomax.w", 0b10100_0_0_00000_00000_010_00000_0101111


class amominu_w(InstrAMO):
    opn, opc = "amominu.w", 0b11000_0_0_00000_00000_010_00000_0101111


class amomaxu_w(InstrAMO):
    opn, opc = "amomaxu.w", 0b11100_0_0_00000_00000_010_00000_0101111


class lr_d(InstrR):
    opn, opc = "lr.d", 0b00010_0_0_00000_00000_011_00000_0101111

    @property
    def is_load(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_pop(self):
        return self.params.inputs['rs1'].number == 2


class sc_d(InstrR):
    opn, opc = "sc.d", 0b00011_0_0_00000_00000_011_00000_0101111

    @property
    def is_store(self):
        return self.params.inputs['rs1'].number != 2

    @property
    def is_push(self):
        return self.params.inputs['rs1'].number == 2


class amoswap_d(InstrAMO):
    opn, opc = "amoswap.d", 0b00001_0_0_00000_00000_011_00000_0101111


class amoadd_d(InstrAMO):
    opn, opc = "amoadd.d", 0b00000_0_0_00000_00000_011_00000_0101111


class amoxor_d(InstrAMO):
    opn, opc = "amoxor.d", 0b00100_0_0_00000_00000_011_00000_0101111


class amoand_d(InstrAMO):
    opn, opc = "amoand.d", 0b01100_0_0_00000_00000_011_00000_0101111


class amoor_d(InstrAMO):
    opn, opc = "amoor.d", 0b01000_0_0_00000_00000_011_00000_0101111


class amomin_d(InstrAMO):
    opn, opc = "amomin.d", 0b10000_0_0_00000_00000_011_00000_0101111


class amomax_d(InstrAMO):
    opn, opc = "amomax.d", 0b10100_0_0_00000_00000_011_00000_0101111


class amominu_d(InstrAMO):
    opn, opc = "amominu.d", 0b11000_0_0_00000_00000_011_00000_0101111


class amomaxu_d(InstrAMO):
    opn, opc = "amomaxu.d", 0b11100_0_0_00000_00000_011_00000_0101111


# A
instructionsA = [
    lr_w,
    sc_w,
    amoswap_w,
    amoadd_w,
    amoxor_w,
    amoand_w,
    amoor_w,
    amomin_w,
    amomax_w,
    amominu_w,
    amomaxu_w,
]

if xlen == 64:
    instructionsA += [
        lr_d,
        sc_d,
        amoswap_d,
        amoadd_d,
        amoxor_d,
        amoand_d,
        amoor_d,
        amomin_d,
        amomax_d,
        amominu_d,
        amomaxu_d,
    ]
