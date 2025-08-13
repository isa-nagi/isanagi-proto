from isana.compiler import LLVMCompiler


class RiscvXCompiler(LLVMCompiler):
    target = "RiscvXpu"
    triple = "riscvxpu32le-unknown-elf"

    def __init__(self, isa, **kwargs):
        super().__init__(isa, **kwargs)


compiler = RiscvXCompiler
