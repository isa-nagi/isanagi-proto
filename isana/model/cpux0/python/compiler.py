from isana.compiler import Fixup
from isana.compiler import LLVMCompiler


class rel32(Fixup):
    name = "rel32"


class CpuX0Compiler(LLVMCompiler):
    namespace = "CpuX0"
    triple = ("cpux0", "", "")

    fixups = (
        # rel32,
    )

    def __init__(self, isa):
        super().__init__(isa)


compiler = CpuX0Compiler
