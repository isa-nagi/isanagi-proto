import argparse
from okojo.elf import ElfObject
from okojo.disasm import DisassemblyObject
from isana.model.riscv.python.isa import isa
from uguisu.graph import TextNode, Edge, Graph


def build_callgraph(dis):
    graph = Graph()
    node_table = dict()
    for func in dis.functions:
        text = str(func.labels)
        node = TextNode(data=text)
        node.margin.y = 80
        graph.add_node(node)
        node_table[func] = node
    for func in dis.functions:
        n0 = node_table[func]
        for tgt in func.call_tgts + func.cyclic_call_tgts:
            n1 = node_table[tgt]
            edge = Edge(n0, n1)
            graph.add_edge(edge)
    graph.arrange()
    return graph


def collect_stack_size(dis):
    stack_sizes = dict()
    for func in dis.functions:
        stack_sizes.setdefault(func, dict())
        stack_sizes[func].setdefault('self', 0)
        stack_sizes[func].setdefault('children', 0)
    for func, gofoward in dis.walk_functions_by_depth():
        if gofoward:
            continue
        max_sp = 0
        for op in func.operators:
            match0 = False
            match1 = False
            for param in op.ins.params.outputs.values():
                reg = dis.isa.get_reg(param.type_, param.number)
                if reg and reg.is_stack_pointer:
                    match0 = True
                    break
            if op.ins.is_push or op.ins.is_pop:
                match1 = True
            if not (match0 or match1):
                continue
            for param in op.ins.params.inputs.values():
                if dis.isa.is_imm_type(param.type_):
                    max_sp = max(max_sp, param.value)
        stack_sizes[func]['self'] = max_sp
        for tgt in func.call_tgts:
            stack_sizes[func]['children'] += stack_sizes[tgt]['self'] + stack_sizes[tgt]['children']
    return stack_sizes


def collect_using_registers(dis):
    regs = dict()
    for func in dis.functions:
        regs.setdefault(func, dict())
        regs[func].setdefault('func', func)
        regs[func].setdefault('self', {'callee': list(), 'caller': list()})
        regs[func].setdefault('children', {'callee': list(), 'caller': list()})
    for func, gofoward in dis.walk_functions_by_depth():
        if gofoward:
            continue
        for op in func.operators:
            params = list(op.ins.params.outputs.values())
            params += list(op.ins.params.inputs.values())
            for param in params:
                reg = dis.isa.get_reg(param.type_, param.number)
                if not reg:
                    continue
                rfs = regs[func]['self']
                is_push_pop = op.ins.is_push or op.ins.is_pop
                if not is_push_pop and reg.is_callee_saved and reg.number not in [r.number for r in rfs['callee']]:
                    rfs['callee'].append(reg)
                if not is_push_pop and reg.is_caller_saved and reg.number not in [r.number for r in rfs['caller']]:
                    rfs['caller'].append(reg)
                rfs['callee'].sort(key=lambda r: r.number)
                rfs['caller'].sort(key=lambda r: r.number)
        rfc = regs[func]['children']
        for tgt in func.call_tgts:
            rts = regs[tgt]['self']
            for tr in rts['callee']:
                if tr.number not in [r.number for r in rfc['callee']]:
                    rfc['callee'].append(tr)
            for tr in rts['caller']:
                if tr.number not in [r.number for r in rfc['caller']]:
                    rfc['caller'].append(tr)
            rtc = regs[tgt]['children']
            for tr in rtc['callee']:
                if tr.number not in [r.number for r in rfc['callee']]:
                    rfc['callee'].append(tr)
            for tr in rtc['caller']:
                if tr.number not in [r.number for r in rfc['caller']]:
                    rfc['caller'].append(tr)
        rfc['callee'].sort(key=lambda r: r.number)
        rfc['caller'].sort(key=lambda r: r.number)
    return regs


def collect_calls(dis):
    calls = dict()
    for func in dis.functions:
        calls.setdefault(func, dict())
        calls[func].setdefault('func', func)
        # calls[func]['calls'] = [f for f, g in func.walk_functions_by_depth() if g and f != func]
        calls[func]['called'] = list(set(func.call_srcs[:]))
        calls[func].setdefault('calltree', list())
        for f, gofoward in func.walk_functions_by_depth():
            if gofoward and f != func:
                calls[func]['calltree'].append(f)
                # calls[f].setdefault('func', f)
                # calls[f].setdefault('called', list())
                # calls[f]['called'].append(func)
    return calls


def collect_callgraph_info(dis):
    stack_sizes = collect_stack_size(dis)
    using_regs = collect_using_registers(dis)
    calls = collect_calls(dis)
    info = dict()
    for func in dis.functions:
        info[func] = dict()
        info[func]['func'] = func
        info[func]['stack_size'] = stack_sizes[func]
        info[func]['using_regs'] = using_regs[func]
        info[func]['calls'] = calls[func]
    return info


def write_callgraph_info(info, file):
    for func in info.keys():
        regs = info[func]['using_regs']
        stack_size = info[func]['stack_size']
        calls = info[func]['calls']
        print("{}:".format(func.label), file=file)
        print("  call tree : {}".format([f.label for f in calls['calltree']]), file=file)
        print("  called from : {}".format([f.label for f in calls['called']]), file=file)
        print("  stack (self)     : {}".format(stack_size['self']), file=file)
        print("  stack (children) : {}".format(stack_size['children']), file=file)
        print("  callee-regs (self)     : {}".format(
            ' '.join([r.label for r in regs['self']['callee']])), file=file)
        print("  callee-regs (children) : {}".format(
            ' '.join([r.label for r in regs['children']['callee']])), file=file)
        print("  caller-regs (self)     : {}".format(
            ' '.join([r.label for r in regs['self']['caller']])), file=file)
        print("  caller-regs (children) : {}".format(
            ' '.join([r.label for r in regs['children']['caller']])), file=file)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--toolchain', default=None, type=str)
    argparser.add_argument('--machine', default=None, type=str)
    argparser.add_argument('--vertical', default=False, action='store_true')
    argparser.add_argument('--max-depth', '-d', default=20, type=int)
    argparser.add_argument('elf')
    args = argparser.parse_args()
    elfpath = args.elf

    elf = ElfObject(elfpath)
    elf.read_all()

    dis = DisassemblyObject(elf, isa)

    graph = build_callgraph(dis)
    fname = elfpath + ".callgraph.html"
    with open(fname, "w") as f:
        s = graph.to_svg(html=True)
        f.write(s)

    info = collect_callgraph_info(dis)
    fname = elfpath + ".callgraph.txt"
    with open(fname, "w") as f:
        write_callgraph_info(info, file=f)


if __name__ == '__main__':
    main()
