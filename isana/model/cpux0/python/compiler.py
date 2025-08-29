from isana.compiler import LLVMCompiler

from .uarch import processors


class CpuX0Compiler(LLVMCompiler):
    namespace = "CpuX0"
    triple = ("cpux0", "", "")
    processors = processors

    def __init__(self, isa):
        super().__init__(isa)


compiler = CpuX0Compiler
