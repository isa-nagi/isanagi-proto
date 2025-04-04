from isana.isa import ISA
from isana.isa import Context

from .memory import Mem
from .register import GPR, SR, C0R, SPR
from .datatype import Imm, ImmS12, ImmS16, ImmS16O16, ImmS24
from .instruction import instructions

from .compiler import compiler


class CpuX0Context(Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def pre_semantic(self):
        pass

    def post_semantic(self, ins):
        is_jump = any([
            ins.is_jump, ins.is_branch, ins.is_call, ins.is_tail, ins.is_return
        ])
        if not is_jump:
            self.C0R.pc = self.C0R.pc + 4


class CpuX0ISA(ISA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


isa = CpuX0ISA(
    name="cpux0",
    endian="little",
    registers=(
        GPR,
        SR,
        C0R,
        SPR,
    ),
    memories=(
        Mem,
    ),
    immediates=(
        Imm,
        ImmS12,
        ImmS16,
        ImmS16O16,
        ImmS24,
    ),
    instructions=instructions,
    compiler=compiler,
    context=CpuX0Context,
)
