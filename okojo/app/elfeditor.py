import argparse
import os
import re
import sys
from okojo.elf import ElfObject


def main():
    argparser = argparse.ArgumentParser()
    # argparser.add_argument('--isa-dir', default=".", type=str)
    argparser.add_argument('-c', dest='commands', action='append')
    argparser.add_argument('-o', dest='output', default="", type=str)
    argparser.add_argument('elf')
    args = argparser.parse_args()
    elfpath = args.elf

    elf = ElfObject(elfpath)
    elf.read_all()

    if args.output:
        abs_input = os.path.abspath(args.elf)
        abs_output = os.path.abspath(args.output)
        if abs_input == abs_output:
            print('Error: output file is same as input file', file=sys.stderr)
            sys.exit(1)
        outfpath = args.output
    else:
        outfpath = args.elf + ".edit"

    commands = args.commands[:]
    while len(commands) > 0:
        cmd = commands.pop(0)
        print("cmd:", cmd)
        if m := re.match(r'(.+)=(.+)', cmd):
            key, value = m.groups()
            if key[:3] == 'eh.':
                if key[3:] in ElfObject.EH.ei_key + ElfObject.EH.e_key:
                    v = getattr(elf.eh, key[3:])
                    print('-|', v)
                    setattr(elf.eh, key[3:], int(value))
                    v = getattr(elf.eh, key[3:])
                    print('+|', v)

    with open(outfpath, 'wb') as f:
        elf.write(f)


if __name__ == '__main__':
    main()
