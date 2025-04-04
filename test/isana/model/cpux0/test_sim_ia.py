from isana.model.cpux0.python.isa import isa  # noqa


def test_decode():
    isa.new_context()
    ctx = isa._ctx

    ctx.Mem.write(32, 0x0000_0000, 0b10000000000000000001_10001_0110111)  # lui x17, 0x80001000

    isa.execute(addr=0x0000_0000)
    isa.execute()
    for reg in ctx.GPR:
        print(reg.label, hex(reg.value))


if __name__ == '__main__':
    test_decode()
