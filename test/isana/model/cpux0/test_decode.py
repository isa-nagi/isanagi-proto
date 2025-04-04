from isana.model.cpux0.python.isa import isa  # noqa


def test_decode():
    values32 = (
        0b10000000000000000001_10001_0110111,  # lui
    )
    values = [v.to_bytes(4, "little") for v in values32]

    for value in values:
        instr = isa.decode(value)
        print(instr, instr.bitsize)


if __name__ == '__main__':
    test_decode()
