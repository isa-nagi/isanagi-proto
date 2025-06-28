import ast
import inspect
from textwrap import dedent


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
    ast.Add: "add",
    ast.Sub: "sub",
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

    def __repr__(self):
        s = "{}(picks={})".format(
            self.__class__.__name__,
            str([get_ast_name(a) for a in self.picks]),
        )
        return s


def get_ast_name(obj):
    if type(obj) is ast.Name:
        return obj.id
    if type(obj) is ast.Attribute:
        # return "{}.{}".format(obj.value.id, obj.attr)
        return obj.attr
    if type(obj) is ast.Subscript:
        # return "{}[{}]".format(get_ast_name(obj.value), get_ast_name(obj.slice))
        return get_ast_name(obj.slice)
    if type(obj) in (ast.Pow, ast.NotEq):
        return obj.__class__.__name__
    return "UnknownAst:" + obj.__class__.__name__

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
            # Note: Nn Attribute, the right side of "." is the parent.
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


def may_change_pc_absolute(instr):
    def pcabs_semantic(self, ctx, ins):
        PickAny.pc = PickAny
    def pcabs_ng1_semantic(self, ctx, ins):
        PickAny.pc + Any
    def pcabs_ng2_semantic(self, ctx, ins):
        Any + PickAny.pc

    semantic = instr.semantic
    if m := _search_ast(semantic, pcabs_semantic):
        try:
            grpn = m.picks[0].attr
            is_pc = eval(f'instr.isa._ctx.{grpn}.get_obj("pc").is_pc')
        except Exception:
            is_pc = False
        rhs = m.picks[1]
        if is_pc:
            is_pc1 = is_pc2 = False
            if m_ng1 := _match_ast(rhs, pcabs_ng1_semantic):
                try:
                    grpn = m_ng1.picks[1].attr
                    is_pc1 = eval(f'instr.isa._ctx.{grpn}.get_obj("pc").is_pc')
                except Exception:
                    is_pc1 = False
            if m_ng2 := _match_ast(rhs, pcabs_ng2_semantic):
                try:
                    grpn = m_ng2.picks[1].attr
                    is_pc2 = eval(f'instr.isa._ctx.{grpn}.get_obj("pc").is_pc')
                except Exception:
                    is_pc2 = False
            if not (is_pc1 or is_pc2):
                return ast.unparse(m.picks[1])
    return None


def may_change_pc_relative(instr):
    def pcrel1_semantic(self, ctx, ins):
        PickAny = PickAny + PickAny  # noqa
    def pcrel2_semantic(self, ctx, ins):
        PickAny += PickAny  # noqa

    semantic = instr.semantic
    if m := _search_ast(semantic, pcrel1_semantic):
        try:
            regn0 = m.picks[0].attr
            grpn0 = m.picks[0].value.attr
            is_pc0 = eval(f'instr.isa._ctx.{grpn0}.get_obj("{regn0}").is_pc')
            regn1 = m.picks[1].attr
            grpn1 = m.picks[1].value.attr
            is_pc1 = eval(f'instr.isa._ctx.{grpn1}.get_obj("{regn1}").is_pc')
        except Exception:
            is_pc0 = is_pc1 = False
        if is_pc0 and is_pc1:
            return ast.unparse(m.picks[2])
    if m := _search_ast(semantic, pcrel2_semantic):
        try:
            m.picks[0]  # ctx.PC.pc
            m.picks[1]  # imm
            regn = m.picks[0].attr
            grpn = m.picks[0].value.attr
            is_pc = eval(f'instr.isa._ctx.{grpn}.get_obj("{regn}").is_pc')
        except Exception:
            is_pc = False
        if is_pc:
            return ast.unparse(m.picks[1])
    return None


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
    def unsigned():
        pass
    def imm_term_semantic(self, ctx, ins):
        # ins.PickAny
        ins.Pick
    def unsigned_imm_term_semantic(self, ctx, ins):
        # unsigned(Any, ins.PickAny)
        unsigned(Any, ins.Pick)
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
        # rhs_r_name = "imm"
        rhs_r_name = get_ast_name(mr.picks[0])
        rhs_r_unsigned = False
    elif mr := _match_ast(rhs_r, _strip_expr(unsigned_imm_term_semantic)):
        rhs_r_tp = "UnknownImm"
        # rhs_r_name = "imm"
        rhs_r_name = get_ast_name(mr.picks[0])
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
        ctx.GPR[Any] = ins.Pick

    m = _match_ast(semantic, li_semantic)
    return m


def estimate_load_immediate_ops(isa):
    li32 = None
    li_s = []
    lui_s = []
    addi_s = []
    for cls in isa.instructions:
        instr = cls()
        instr.isa = isa
        instr.decode(instr.opc)  # dummy decode as all parameter is 0
        if m := may_load_immediate(instr.semantic):
            # r_tp = instr.params.inputs["imm"].type_
            imm_key = get_ast_name(m.picks[0])
            r_tp = instr.params.inputs[imm_key].type_
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
            # if op == "add" and r_name == "imm":
            if op == "add" and r_tp == "UnknownImm":
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
            # r_tp = op.params.inputs["imm"].type_
            # imm = next(filter(lambda im: im.label == r_tp, isa.immediates), None)
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


def estimate_add_immediate_codes(isa):
    def get_cond(imm):
        cond = "!(Amount & {mask}) && ({minv} <= (Amount>>{shift})) && ((Amount>>{shift}) <= {maxv})".format(
            mask=int(pow(2, imm.offset) - 1),
            shift=imm.offset,
            minv=-int(pow(2, imm.width)),
            maxv=int(pow(2, imm.width) - 1),
        )
        return cond

    li_ops = estimate_load_immediate_ops(isa)
    (li32, li_s, lui_s, addi_s, lui_addi_s) = li_ops
    codes = list()
    for ops in li_s + lui_s + addi_s + (li32,):
        vardefs = []
        buildmis = []
        if isinstance(ops[0], tuple):
            lui_op, lui_imm = ops[0]
            lui_opname = lui_op.opn.upper()
            addi_op, addi_imm = ops[1]
            addi_opname = addi_op.opn.upper()
            # lui
            vardef = "Register TempReg = MRI.createVirtualRegister(&{Xpu}::GPRRegClass);"
            vardefs.append(vardef)
            vardef = "Register ImmReg = MRI.createVirtualRegister(&{Xpu}::GPRRegClass);"
            vardefs.append(vardef)
            if hasattr(addi_imm, "signed"):
                vardef = "int64_t Hi = ((Amount + {half}) >> {shift}) & {mask};".format(
                    half=2 ** (lui_imm.offset - 1),
                    shift=lui_imm.offset,
                    mask=2 ** lui_imm.width - 1,
                )
            else:
                vardef = "int64_t Hi = ((Amount >> {shift})) & {mask};".format(
                    shift=lui_imm.offset,
                    mask=2 ** lui_imm.width - 1,
                )
            vardefs.append(vardef)
            buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::{lui_opname}), TempReg)"
            for param in lui_op.params.inputs.values():
                if isa.is_imm_type(param.type_):
                    buildmi += ".addImm(Hi)"
                else:
                    buildmi += f"/*{param} {param.type_}*/ "
            buildmi += ";"
            buildmis.append(buildmi)
            # addi
            vardef = "int64_t Lo = Amount & {mask};".format(
                mask=2 ** addi_imm.width - 1,
            )
            vardefs.append(vardef)
            buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::{addi_opname}), ImmReg)"
            for param in addi_op.params.inputs.values():
                if isa.is_reg_type(param.type_):
                    buildmi += ".addReg(TempReg, RegState::Kill)"
                elif isa.is_imm_type(param.type_):
                    buildmi += ".addImm(Lo)"
                else:
                    buildmi += f"/*{param} {param.type_}*/ "
            buildmi += ";"
            buildmis.append(buildmi)
            # add
            buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::ADD), DstReg)"  # noqa
            buildmi += ".addReg(SrcReg)"
            buildmi += ".addReg(ImmReg, RegState::Kill)"
            buildmi += ";"
            buildmis.append(buildmi)

            cond = "else"
            codes.append((cond, vardefs, buildmis))
        else:
            op, imm = ops
            cond = get_cond(imm)
            cond = f"if (/*{imm.label}*/ {cond})"
            if len(codes) > 0:
                cond = "else " + cond
            opname = op.opn.upper()
            if ops in li_s or ops in lui_s:
                # l[u]i : l[u]i t, hi(amount); add dst, src, t
                vardef = "Register TempReg = MRI.createVirtualRegister(&{Xpu}::GPRRegClass);"
                vardefs.append(vardef)
                if ops in lui_s:
                    vardef = "int64_t Hi = ((Amount >> {shift})) & {mask};".format(
                        shift=imm.offset,
                        mask=2 ** imm.width - 1,
                    )
                    vardefs.append(vardef)
                # l[u]i
                buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::{opname}), TempReg)"
                for param in op.params.inputs.values():
                    if isa.is_imm_type(param.type_):
                        if ops in lui_s:
                            buildmi += ".addImm(Hi)"
                        else:
                            buildmi += ".addImm(Amount)"
                    else:
                        buildmi += f"/*{param} {param.type_}*/ "
                buildmi += ";"
                # add
                buildmis.append(buildmi)
                buildmi = "BuildMI(MBB, MBBI, DL, get({Xpu}::ADD), DstReg)"
                buildmi += ".addReg(SrcReg)"
                buildmi += ".addReg(TempReg)"
                buildmi += ";"
                buildmis.append(buildmi)
            else:
                # addi  : addi dst, src, amount;
                buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::{opname}), DstReg)"
                for param in op.params.inputs.values():
                    if isa.is_reg_type(param.type_):
                        buildmi += ".addReg(SrcReg)"
                    elif isa.is_imm_type(param.type_):
                        buildmi += ".addImm(Amount)"
                    else:
                        buildmi += f"/*{param} {param.type_}*/ "
                buildmi += ";"
                buildmis.append(buildmi)
            codes.append((cond, vardefs, buildmis))
    return codes


def estimate_selectaddr_codes(isa, has_addr):
    def get_cond(imm):
        cond = "!(CVal & {mask}) && ({minv} <= (CVal>>{shift})) && ((CVal>>{shift}) <= {maxv})".format(
            mask=int(pow(2, imm.offset) - 1),
            shift=imm.offset,
            minv=-int(pow(2, imm.width)),
            maxv=int(pow(2, imm.width) - 1),
        )
        return cond

    li_ops = estimate_load_immediate_ops(isa)
    (li32, li_s, lui_s, addi_s, lui_addi_s) = li_ops
    codes = list()
    for ops in addi_s + lui_addi_s:
        vardefs = []
        sdvalues = []
        if isinstance(ops[0], tuple):
            lui_op, lui_imm = ops[0]
            addi_op, addi_imm = ops[1]
            cond = "else"
            vardef = "int64_t Lo = CVal & {mask};".format(
                mask=2 ** addi_imm.width - 1,
            )
            vardefs.append(vardef)
            vardef = "int64_t Hi = ((CVal >> {shift})) & {mask};".format(
                shift=lui_imm.offset,
                mask=2 ** lui_imm.width - 1,
            )
            vardefs.append(vardef)
            sdvalue = ("auto Lui = SDValue(CurDAG->getMachineNode({Xpu}::LUI, DL, VT, "
                       "CurDAG->getTargetConstant(Hi, DL, VT)), 0);")
            sdvalues.append(sdvalue)
            if has_addr:
                sdvalue = ("Base = SDValue(CurDAG->getMachineNode({Xpu}::ADD, DL, VT, "
                           "Addr.getOperand(0), Lui), 0);")
                sdvalues.append(sdvalue)
            else:
                sdvalue = ("Base = Lui;")
                sdvalues.append(sdvalue)
            sdvalue = "Offset = CurDAG->getTargetConstant(Lo, DL, VT);"
            sdvalues.append(sdvalue)
            codes.append((cond, vardefs, sdvalues))
        else:
            op, imm = ops
            cond = get_cond(imm)
            cond = f"if (/*{imm.label}*/ {cond})"
            if len(codes) > 0:
                cond = "else " + cond
            # addi  : addi dst, src, amount;
            if has_addr:  # (add addr, imm) -> (addr, imm)
                sdvalue = "Base = Addr.getOperand(0);"
                sdvalues.append(sdvalue)
                sdvalue = "Offset = CurDAG->getTargetConstant(CVal, DL, VT);"
                sdvalues.append(sdvalue)
            else:  # (imm) -> (zero, imm)
                sdvalue = "Base = CurDAG->getRegister({Xpu}::{REG0}, VT);"
                sdvalues.append(sdvalue)
                sdvalue = "Offset = CurDAG->getTargetConstant(CVal, DL, VT);"
                sdvalues.append(sdvalue)
            codes.append((cond, vardefs, sdvalues))
    return codes
