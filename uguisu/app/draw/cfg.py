import argparse
import os
import re
from okojo.elf import ElfObject
from okojo.disasm import DisassemblyObject
from isana.model.riscv.python.isa import isa
from uguisu.graph import TextNode, Edge, Graph


def build_cfg(func):
    graph = Graph()
    node_table = dict()
    for block in func.blocks:
        text = '\n'.join("{} {}".format(hex(op.addr), repr(op)) for op in block.operators)
        node = TextNode(data=text)
        graph.add_node(node)
        node_table[block] = node
    for block in func.blocks:
        n0 = node_table[block]
        for tgt in block.jump_tgts + block.cyclic_jump_tgts:
            n1 = node_table[tgt]
            edge = Edge(n0, n1)
            graph.add_edge(edge)
    graph.arrange()
    return graph


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--toolchain', default=None, type=str)
    argparser.add_argument('--machine', default=None, type=str)
    argparser.add_argument('--vertical', default=False, action='store_true')
    argparser.add_argument('--max-depth', '-d', default=20, type=int)
    argparser.add_argument('--func', '-f', default=None)
    argparser.add_argument('elf')
    args = argparser.parse_args()
    elfpath = args.elf

    elf = ElfObject(elfpath)
    elf.read_all()

    dis = DisassemblyObject(elf, isa)

    # vertical = args.vertical
    # max_depth = args.max_depth
    funcs = list()
    if args.func is None:
        funcs = dis.functions[:]
    else:
        for fn in dis.functions:
            if re.match(args.func, fn.label):
                funcs.append(fn)
                break
        else:
            raise ValueError('funcion not found: "%s"' % args.func)

    dirname = elfpath + ".cfg"
    os.makedirs(dirname, exist_ok=True)

    for func in funcs:
        print("[func]", func.label)
        graph = build_cfg(func)
        fname = os.path.join(dirname, "{}.html".format(func.label_escape))
        with open(fname, "w") as f:
            s = graph.to_svg(html=True, title="CFG")
            f.write(s)


if __name__ == '__main__':
    main()
