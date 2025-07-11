from isana.model.riscvx.python.isa import isa  # noqa


def test_decode():
    isa.new_context()
    ctx = isa._ctx

    ctx.Mem.write(32, 0x0000_0000, 0b10000000000000000001_10001_0110111)  # lui x17, 0x80001000
    ctx.Mem.write(32, 0x0000_0004, 0b100000000001_10001_000_10101_0010011)  # addi x21, x17, -0x7ff

    isa.execute(addr=0x0000_0000)
    isa.execute()
    for reg in ctx.GPR:
        print(reg.label, hex(reg.value))


if __name__ == '__main__':
    test_decode()
