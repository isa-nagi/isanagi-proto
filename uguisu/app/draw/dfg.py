import os
import re
from okojo.elf import ElfObject
from okojo.disasm import DisassemblyObject
from isana.isa import load_isa
from uguisu.graph import TextNode, Edge, Graph


def add_args(subparsers):
    parser = subparsers.add_parser('dfg')
    parser.add_argument('--isa-dir', default=".", type=str)
    parser.add_argument('--vertical', default=False, action='store_true')
    parser.add_argument('--max-depth', '-d', default=20, type=int)
    parser.add_argument('--func', '-f', default=None)
    parser.add_argument('elf')


def build_dfg(func):
    graph = Graph()
    node_table = dict()
    for op in func.operators:
        text = "{} {}".format(hex(op.addr), repr(op))
        node = TextNode(data=text)
        graph.add_node(node)
        node_table[op] = node
    func_operators = list(func.operators)
    for i, op in enumerate(func_operators):
        n0 = node_table[op]
        if i + 1 < len(func_operators):
            op1 = func_operators[i + 1]
            if op.block == op1.block:
                n1 = node_table[op1]
                edge = Edge(n0, n1)
                graph.add_edge(edge)
        for dst in op.data_dsts:  # + op.cyclic_data_dsts:
            n1 = node_table[dst]
            edge = Edge(n0, n1)
            graph.add_edge(edge)
    graph.arrange()
    return graph


def main(args):
    elfpath = args.elf

    isa = load_isa(args.isa_dir)

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

    dirname = elfpath + ".dfg"
    os.makedirs(dirname, exist_ok=True)

    for func in funcs:
        print("[func]", func.label)
        graph = build_dfg(func)
        fname = os.path.join(dirname, "{}.html".format(func.label_escape))
        with open(fname, "w") as f:
            s = graph.to_svg(html=True, title="DFG")
            f.write(s)


if __name__ == '__main__':
    main()
