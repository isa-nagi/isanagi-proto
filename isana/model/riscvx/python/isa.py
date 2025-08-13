from isana.isa import ISA
from isana.isa import Context
# from isana.isa import signed
# from isana.isa import unimpl

from .memory import Mem
from .register import PCR, GPR, GPRC, FPR, CSR
from .datatype import (Imm, ImmS12, ImmS12O1, ImmS20O1, ImmS20O12, ImmS6, ImmS9, ImmS32O2,
                       ImmS5O2, ImmS5O3, ImmS5O4, ImmS11O1, ImmS6O2, ImmS6O3, ImmS6O4, ImmS8O1,
                       ImmS2O4, ImmU4,
                       RMImm)
from .instruction import instructions

from .abi import abi
from .compiler import compiler


class RiscvXContext(Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def pre_semantic(self):
        self.PCR.prev_pc = self.PCR.pc

    def post_semantic(self, ins):
        is_jump = any([
            ins.is_jump, ins.is_branch, ins.is_call, ins.is_tail, ins.is_return
        ])
        if not is_jump:
            self.PCR.pc = self.PCR.pc + 4


class RiscvXISA(ISA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


isa = RiscvXISA(
    name="RiscvX",
    registers=(
        PCR,
        GPR,
        GPRC,
        FPR,
        CSR,
    ),
    memories=(
        Mem,
    ),
    immediates=(
        Imm,
        ImmS12,
        ImmS12O1,
        ImmS20O1,
        ImmS20O12,
        ImmS6,
        ImmS9,
        ImmS32O2,
        ImmS5O2,
        ImmS5O3,
        ImmS5O4,
        ImmS11O1,
        ImmS6O2,
        ImmS6O3,
        ImmS6O4,
        ImmS8O1,
        ImmS2O4,
        ImmU4,
        RMImm,
    ),
    instructions=tuple(instructions),
    abi=abi,
    compiler=compiler,
    context=RiscvXContext,
)
