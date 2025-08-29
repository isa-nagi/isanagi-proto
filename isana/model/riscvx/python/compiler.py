from isana.compiler import LLVMCompiler

from .uarch import processors


class RiscvXCompiler(LLVMCompiler):
    target = "RiscvXpu"
    triple = "riscvxpu32le-unknown-elf"
    processors = processors

    def __init__(self, isa, **kwargs):
        super().__init__(isa, **kwargs)


compiler = RiscvXCompiler
