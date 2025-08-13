from okojo.elf import ElfObject
from okojo.disasm import DisassemblyObject
from isana.model.riscvx.python.isa import isa
import os


def main():
    curdir = os.path.dirname(os.path.abspath(__file__))
    elfpath = os.path.join(curdir, "src", "test1-gcc-rv32i.elf")
    elf = ElfObject(elfpath)
    elf.read_all()

    dis = DisassemblyObject(elf, isa)

    # with open(elfpath + '.json', 'w') as f:
    import pprint
    pprint.pprint(dis.to_json())


if __name__ == "__main__":
    main()
