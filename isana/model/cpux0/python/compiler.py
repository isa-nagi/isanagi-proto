from isana.compiler import LLVMCompiler


class CpuX0Compiler(LLVMCompiler):
    namespace = "CpuX0"
    triple = ("cpux0", "", "")

    def __init__(self, isa):
        super().__init__(isa)


compiler = CpuX0Compiler
