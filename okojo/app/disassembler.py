import argparse
import sys
from okojo.elf import ElfObject
from okojo.disasm import DisassemblyObject
from isana.model.riscv.python.isa import isa


def print_dis(dis, file=None):
    if file is None:
        file = sys.stdout
    max_bytesize = max([op.ins.bytesize for op in dis.operators])
    for func in dis.functions:
        print("", file=file)
        print("{}:".format(func.label), file=file)
        for op in func.operators:
            op_bytes = [
                '{:02x}'.format(v) for v in op.binary.to_bytes(op.ins.bytesize)
            ]
            if len(op_bytes) < max_bytesize:
                op_bytes += ['  '] * (max_bytesize - len(op_bytes))
            print("  {:08x}  {}    {}".format(
                op.addr,
                ' '.join(op_bytes),
                op,
            ), file=file)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--toolchain', default=None, type=str)
    argparser.add_argument('--machine', default=None, type=str)
    argparser.add_argument('elf')
    args = argparser.parse_args()
    elfpath = args.elf

    elf = ElfObject(elfpath)
    elf.read_all()

    dis = DisassemblyObject(elf, isa)

    outfname = elfpath + ".dis2"
    with open(outfname, "w") as f:
        print_dis(dis, f)


if __name__ == '__main__':
    main()
