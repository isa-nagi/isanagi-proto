from isana.abi import ABI


class CpuX0ABI(ABI):
    def __init__(self, isa, **kwargs):
        super().__init__(isa, **kwargs)


abi = CpuX0ABI
