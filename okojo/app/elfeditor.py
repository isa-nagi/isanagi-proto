import argparse
import os
import re
import sys
from okojo.elf import ElfObject
from okojo.ar import ArchiveObject


def debug_print(*args, verbose=False, **kwargs):
    if verbose:
        print(*args, **kwargs)


def main():
    argparser = argparse.ArgumentParser()
    # argparser.add_argument('--isa-dir', default=".", type=str)
    argparser.add_argument('-c', dest='commands', action='append')
    argparser.add_argument('-o', dest='output', default="", type=str)
    argparser.add_argument('-v', '--verbose', default=False, action='store_true')
    argparser.add_argument('elf')
    args = argparser.parse_args()
    elfpath = args.elf

    if args.output:
        abs_input = os.path.abspath(args.elf)
        abs_output = os.path.abspath(args.output)
        if abs_input == abs_output:
            print('Error: output file is same as input file', file=sys.stderr)
            sys.exit(1)
        outfpath = args.output
    else:
        outfpath = args.elf + ".edit"

    if ArchiveObject.is_archive(elfpath):
        arf = ArchiveObject(elfpath)
        arf.read_all()
        elfs = []
        for f in arf.files:
            if f.data:
                if ElfObject.is_elf(f.data):
                    elf = ElfObject(f.data)
                    elf.read_all()
                    elfs.append(elf)
    else:
        elf = ElfObject(elfpath)
        elf.read_all()
        elfs = [elf]

    for elf in elfs:
        commands = args.commands[:]
        while len(commands) > 0:
            cmd = commands.pop(0)
            debug_print("cmd:", cmd, verbose=args.verbose)
            if m := re.match(r'(.+)=(.+)', cmd):
                key, value = m.groups()
                if key[:3] == 'eh.':
                    if key[3:] in ElfObject.EH.ei_key + ElfObject.EH.e_key:
                        v = getattr(elf.eh, key[3:])
                        debug_print('-|', v, verbose=args.verbose)
                        setattr(elf.eh, key[3:], int(value))
                        v = getattr(elf.eh, key[3:])
                        debug_print('+|', v, verbose=args.verbose)

    if ArchiveObject.is_archive(elfpath):
        for i, f in enumerate([f for f in arf.files if f.data and ElfObject.is_elf(f.data)]):
            elfs[i].write(f.data)
        with open(outfpath, 'wb') as f:
            arf.write(f)
    else:
        with open(outfpath, 'wb') as f:
            elfs[0].write(f)


if __name__ == '__main__':
    main()
