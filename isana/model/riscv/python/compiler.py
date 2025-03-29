from isana.compiler import Fixup
from isana.compiler import LLVMCompiler


fixups = [
    Fixup(),
]


class RiscvCompiler(LLVMCompiler):
    namespace = "RiscvXpu"
    triplet = ("riscvxpu32", "unknown", "elf")

    def __init__(self, isa, **kwargs):
        super().__init__(isa, **kwargs)


compiler = RiscvCompiler
