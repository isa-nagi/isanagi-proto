import argparse
import sys
from okojo.elf import ElfObject
from okojo.disasm import DisassemblyObject
from isana.isa import load_isa


def print_dis(dis, file=None):
    if file is None:
        file = sys.stdout
    max_bytesize = max([op.ins.bytesize for op in dis.operators])
    for func in dis.functions:
        print("", file=file)
        print("{}:".format(func.label), file=file)
        for op in func.operators:
            op_bytes = [
                '{:02x}'.format(v) for v in op.binary.to_bytes(op.ins.bytesize, "big")
            ]
            if len(op_bytes) < max_bytesize:
                op_bytes += ['  '] * (max_bytesize - len(op_bytes))
            print("  {:08x}  {}    {}".format(
                op.addr,
                ' '.join(op_bytes),
                op._disassemble(),  # op,
            ), file=file)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--isa-dir', default=".", type=str)
    argparser.add_argument('elf')
    args = argparser.parse_args()
    elfpath = args.elf

    isa = load_isa(args.isa_dir)

    elf = ElfObject(elfpath)
    elf.read_all()

    dis = DisassemblyObject(elf, isa)

    outfname = elfpath + ".dis2"
    with open(outfname, "w") as f:
        print_dis(dis, f)


if __name__ == '__main__':
    main()
