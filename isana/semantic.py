import ast
import inspect
from textwrap import dedent
from isana.isa import unsigned


op_alu_table = {
    ast.Add: "add",
    ast.Sub: "sub",
    ast.Mult: "mul",
    ast.FloorDiv: "sdiv",
    ast.Mod: "srem",
    ast.LShift: "shl",
    ast.RShift: "sra",
    ast.BitAnd: "and",
    ast.BitOr: "or",
    ast.BitXor: "xor",
}


op_aluu_table = {
    ast.FloorDiv: "udiv",
    ast.Mod: "urem",
    ast.RShift: "srl",
}

op_cmp_table = {
    ast.Eq: "seteq",
    ast.NotEq: "setne",
    ast.Gt: "setgt",
    ast.Lt: "setlt",
    ast.GtE: "setge",
    ast.LtE: "setle",
}

op_cmpu_table = {
    ast.Gt: "setugt",
    ast.Lt: "setult",
    ast.GtE: "setuge",
    ast.LtE: "setule",
}


Any = None
Pick = None
PickAny = None


class AstMatchObject():
    def __init__(self):
        self.picks = []


def _strip_expr(semantic):
    code = inspect.getsource(semantic)
    code = dedent(code)
    node = ast.parse(code).body[0].body[0].value
    return node

def _match_ast(src, dst):
    if callable(src):
        srccode = inspect.getsource(src)
        srccode = dedent(srccode)
        srcbody = ast.parse(srccode).body[0].body
        # print(ast.dump(ast.parse(srccode), indent=4))
    else:
        srcbody = [src]
    if callable(dst):
        dstcode = inspect.getsource(dst)
        dstcode = dedent(dstcode)
        dstbody = ast.parse(dstcode).body[0].body
        # print(ast.dump(ast.parse(dstcode), indent=4))
    else:
        dstbody = [dst]

    src_ites = [iter(srcbody)]
    dst_ites = [iter(dstbody)]
    return _match_ast_line(src_ites, dst_ites)


def _search_ast(src, dst):
    if callable(src):
        srccode = inspect.getsource(src)
        srccode = dedent(srccode)
        srcbody0 = ast.parse(srccode).body[0]
        srcbodys = [srcbody0.body]
    else:
        srcbody0 = src
        srcbodys = [[src]]
    if callable(dst):
        dstcode = inspect.getsource(dst)
        dstcode = dedent(dstcode)
        dstbody = ast.parse(dstcode).body[0].body
    else:
        dstbody = [dst]

    for node in ast.walk(srcbody0):
        if hasattr(node, "body"):
            srcbodys += [node.body]
    for srcbody in srcbodys:
        for i in range(len(srcbody)):
            src_ites = [iter(srcbody[i:])]
            dst_ites = [iter(dstbody)]
            ret = _match_ast_line(src_ites, dst_ites)
            if ret:
                return ret
    return None


def _match_ast_line(src_ites, dst_ites):
    mobj = AstMatchObject()
    while True:
        try:
            srcv = next(src_ites[-1])
            dstv = next(dst_ites[-1])
        except Exception:
            src_ites.pop()
            dst_ites.pop()
            if len(dst_ites) == 0:
                # if len(src_ites) > 0:
                #     return None
                break
            continue
        # match
        need_comp = True
        if type(dstv) is ast.Name and dstv.id == "Any":
            continue
        if type(dstv) is ast.Name and dstv.id in ["Pick", "PickAny"]:
            mobj.picks.append(srcv)
            need_comp = False
            if dstv.id == "PickAny":
                continue
        if type(dstv) is ast.Attribute and dstv.attr in ["Pick", "PickAny"]:
            mobj.picks.append(srcv)
            need_comp = False
        if type(dstv) in (ast.Pow, ast.NotEq):
            mobj.picks.append(srcv)
            need_comp = False
        if need_comp:
            if type(srcv) is type(dstv):
                pass
            else:
                return None
        # next
        if isinstance(srcv, list):
            pass
        else:
            src_children = list(ast.iter_child_nodes(srcv))
            dst_children = list(ast.iter_child_nodes(dstv))
            if len(dst_children) > 0:
                src_ites.append(iter(src_children))
                dst_ites.append(iter(dst_children))
    return mobj


def may_change_pc_absolute(semantic):
    def pcabs_semantic(self, ctx, ins):
        ctx.PCR.pc = PickAny
    def pcabs_ng1_semantic(self, ctx, ins):
        ctx.PCR.pc + Any
    def pcabs_ng2_semantic(self, ctx, ins):
        Any + ctx.PCR.pc

    if m := _search_ast(semantic, pcabs_semantic):
        rhs = m.picks[0]
        mng1 = _match_ast(rhs, pcabs_ng1_semantic)
        mng2 = _match_ast(rhs, pcabs_ng2_semantic)
        if not (mng1 or mng2):
            return True
    return False


def may_change_pc_relative(semantic):
    def pcrel1_semantic(self, ctx, ins):
        ctx.PCR.pc = ctx.PCR.pc + Any
    def pcrel2_semantic(self, ctx, ins):
        ctx.PCR.pc += Any

    if _search_ast(semantic, pcrel1_semantic):
        return True
    if _search_ast(semantic, pcrel2_semantic):
        return True
    return False


def may_take_memory_address(semantic):
    code = inspect.getsource(semantic)
    code = dedent(code)
    for node in ast.walk(ast.parse(code)):
        if not (isinstance(node, ast.Attribute) and node.attr in ("read", "write")):
            continue
        if not (isinstance(node.value, ast.Attribute) and node.value.attr == "Mem"):
            continue
        break
    else:
        return False
    return True


def get_alu_dag(semantic):
    def imm_term_semantic(self, ctx, ins):
        ins.imm
    def unsigned_imm_term_semantic(self, ctx, ins):
        unsigned(Any, ins.imm)
    def signed_term_semantic(self, ctx, ins):
        ctx.Pick[PickAny]
    def unsigned_term_semantic(self, ctx, ins):
        unsigned(Any, ctx.Pick[PickAny])
    def alu_semantic(self, ctx, ins):
        ctx.Pick[PickAny] = PickAny ** PickAny
    def mulh_semantic(self, ctx, ins):
        ctx.Pick[PickAny] = (PickAny ** PickAny) << Any
    def cmp_semantic(self, ctx, ins):
        ctx.Pick[PickAny] = PickAny != PickAny

    for dst_semantic in [mulh_semantic, alu_semantic, cmp_semantic]:
        m = _match_ast(semantic, dst_semantic)
        if m:
            break
    else:
        return None
    # print(semantic, dst_semantic)
    dst_tp = m.picks[0].attr
    if isinstance(m.picks[1], ast.Constant):
        dst_name = m.picks[1].value
    else:
        dst_name = m.picks[1].attr
    rhs_l = m.picks[2]
    op_node = m.picks[3]
    rhs_r = m.picks[4]

    # print("A", semantic, dst_semantic)
    if ml := _search_ast(rhs_l, _strip_expr(signed_term_semantic)):
        rhs_l_tp = ml.picks[0].attr
        rhs_l_name = ml.picks[1].attr
        rhs_l_unsigned = False
    elif ml := _search_ast(rhs_l, _strip_expr(unsigned_term_semantic)):
        rhs_l_tp = ml.picks[0].attr
        rhs_l_name = ml.picks[1].attr
        rhs_l_unsigned = True
    else:
        # not rhs_l == ctx.GPR
        return None
    if mr := _match_ast(rhs_r, _strip_expr(signed_term_semantic)):
        rhs_r_tp = mr.picks[0].attr
        rhs_r_name = mr.picks[1].attr
        rhs_r_unsigned = False
    elif mr := _match_ast(rhs_r, _strip_expr(unsigned_term_semantic)):
        rhs_r_tp = mr.picks[0].attr
        rhs_r_name = mr.picks[1].attr
        rhs_r_unsigned = True
    elif mr := _match_ast(rhs_r, _strip_expr(imm_term_semantic)):
        rhs_r_tp = "UnknownImm"
        rhs_r_name = "imm"
        rhs_r_unsigned = False
    elif mr := _match_ast(rhs_r, _strip_expr(unsigned_imm_term_semantic)):
        rhs_r_tp = "UnknownImm"
        rhs_r_name = "imm"
        rhs_r_unsigned = True
    else:
        return None

    if not rhs_r_unsigned and not rhs_l_unsigned:
        if dst_semantic == mulh_semantic:
            dag_op = "mulhs"
        else:
            dag_op = {**op_alu_table, **op_cmp_table}[type(op_node)]
    else:
        if dst_semantic == mulh_semantic:
            if not rhs_r_unsigned:
                dag_op = "mulhsu"
            else:
                dag_op = "mulhu"
        else:
            dag_op = {**op_aluu_table, **op_cmpu_table}[type(op_node)]

    return (
        dag_op,
        (dst_name, dst_tp),
        (rhs_l_name, rhs_l_tp, rhs_l_unsigned),
        (rhs_r_name, rhs_r_tp, rhs_r_unsigned),
    )


def may_load_immediate(semantic):
    def li_semantic(s, ctx, ins):
        ctx.GPR[Any] = ins.imm

    m = _match_ast(semantic, li_semantic)
    return m is not None


def estimate_load_immediate_ops(isa):
    li32 = None
    li_s = []
    lui_s = []
    addi_s = []
    for cls in isa.instructions:
        instr = cls()
        instr.isa = isa
        instr.decode(instr.opc)  # dummy decode as all parameter is 0
        if may_load_immediate(instr.semantic):
            r_tp = instr.params.inputs["imm"].type_
            imm = next(filter(lambda im: im.label == r_tp, isa.immediates), None)
            if imm.offset == 0:
                li_s.append((instr, imm))
                if imm.width == 32:
                    li32 = (instr, imm)
            else:
                lui_s.append((instr, imm))
            continue
        dag = get_alu_dag(instr.semantic)
        if dag:
            (op, (dst_name, dst_tp), (l_name, l_tp, l_u), (r_name, r_tp, r_u)) = dag
            if op == "add" and r_name == "imm":
                r_tp = instr.params.inputs[r_name].type_
                imm = next(filter(lambda im: im.label == r_tp, isa.immediates), None)
                addi_s.append((instr, imm))
    lui_addi_s = []
    for (lui, lui_imm) in lui_s:
        for (addi, addi_imm) in addi_s:
            if lui_imm.offset == addi_imm.width:
                lui_addi_s.append(((lui, lui_imm), (addi, addi_imm)))
                if lui_imm.width + lui_imm.offset == 32 and not li32:
                    li32 = ((lui, lui_imm), (addi, addi_imm))
    return (li32, tuple(li_s), tuple(lui_s), tuple(addi_s), tuple(lui_addi_s))


def _gen_sdnodexform(imm, signed_lower=False):
    if signed_lower:
        half = hex(2 ** (imm.offset - 1)) if imm.offset > 0 else 0
        vstr = f"(N->getZExtValue()+{half})>>{imm.offset}"
        X = "XX"
    else:
        vstr = f"N->getZExtValue()>>{imm.offset}"
        X = "X"
    if hasattr(imm, "signed"):
        vstr = f"SignExtend64<{imm.width}>({vstr})"
    else:
        mask = hex(2 ** imm.width - 1)
        vstr = f"(({vstr}) & {mask})"
    s = "\n".join([
        f"def {imm.label}{X}: SDNodeXForm<imm, [{{",
        "  return CurDAG->getTargetConstant(",
        f"    {vstr},SDLoc(N),N->getValueType(0)",
        "  );",
        "}]>;"
    ])
    return s


def estimate_load_immediate_dag(isa):
    li_ops = estimate_load_immediate_ops(isa)
    (li32, li_s, lui_s, addi_s, lui_addi_s) = li_ops
    zeroreg = None
    for group in isa.registers:
        for reg in group.regs:
            if reg.is_zero:
                zeroreg = reg
                break
    immxs = []
    dags = []
    imm32 = None
    for imm in isa.immediates:
        if imm.width == 32 and imm.offset == 0:
            imm32 = imm
            break
    for ops in (li32,) + li_s + lui_s + addi_s:
        if isinstance(ops[0], tuple):
            # lui
            op, lui_imm = ops[0]
            immtp = lui_imm.label
            lui_str = [op.opn.upper()]
            for param in op.params.inputs.values():
                if param.type_ == immtp:
                    lui_str.append(f"({immtp}XX imm:$imm)")
                else:
                    if zeroreg:
                        lui_str.append(zeroreg.label.upper())
                    else:
                        raise Exception("cannot generate load immediate dag")
            lui_str = " ".join(lui_str)
            # addi
            op, addi_imm = ops[1]
            immtp = addi_imm.label
            opstr = []
            for param in op.params.inputs.values():
                if param.type_ == immtp:
                    opstr.append(f"({immtp}X imm:$imm)")
                else:
                    opstr.append(f"({lui_str})")
            opstr = op.opn.upper() + " " + ", ".join(opstr)
            if ops == li32:
                if imm32:
                    dags.append((imm32.label, opstr))
                else:
                    dags.append(("i32imm", opstr))
            else:
                dags.append((immtp, opstr))
            immx = (lui_imm, hasattr(addi_imm, "signed"))
            if immx not in immxs:
                immxs.append(immx)
            immx = (addi_imm, False)
            if immx not in immxs:
                immxs.append(immx)
        else:
            op, imm = ops
            r_tp = op.params.inputs["imm"].type_
            imm = next(filter(lambda im: im.label == r_tp, isa.immediates), None)
            immtp = imm.label
            opstr = []
            for param in op.params.inputs.values():
                if param.type_ == immtp:
                    opstr.append(f"({immtp}X imm:$imm)")
                else:
                    if zeroreg:
                        opstr.append(zeroreg.label.upper())
                    else:
                        raise Exception("cannot generate load immediate dag")
            opstr = op.opn.upper() + " " + ", ".join(opstr)
            dags.append((immtp, opstr))
            immx = (imm, False)
            if immx not in immxs:
                immxs.append(immx)
    xforms = []
    for immx in immxs:
        imm, signed = immx
        xforms.append(_gen_sdnodexform(imm, signed))
    return xforms, dags
