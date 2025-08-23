import ast
import inspect
import re
import sys
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


class NameReplacer(ast.NodeTransformer):
    def __init__(self, srcids, dstasts):
        super().__init__()
        self.srcids = srcids
        self.dstasts = dstasts

    def visit_Name(self, node):
        if node.id in self.srcids and node.id in self.dstasts:
            return self.dstasts[node.id]
        return node


def resolve_unknown_variable(tgtast, semantic):
    # TODO: This is temporary impl. So make IR for resolve variable correctly.
    if type(tgtast) is ast.Module:
        tgtast = tgtast.body[0]
    if type(tgtast) is ast.Expr:
        tgtast = tgtast.value
    code = inspect.getsource(semantic)
    code = dedent(code)
    var_asts = {}
    for line_ast in ast.parse(code).body[0].body:
        if type(line_ast) is not ast.Assign:
            continue
        if len(line_ast.targets) == 1 and type(line_ast.targets[0]) is ast.Name:
            name = line_ast.targets[0].id
            var_ast = line_ast.value
            var_asts[name] = var_ast
    tgt_names = []
    for node in ast.walk(tgtast):
        if type(node) is ast.Name:
            tgt_names.append(node.id)
    transformer = NameReplacer(tgt_names, var_asts)
    new_tgtast = transformer.visit(tgtast)
    return new_tgtast


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


def may_use_pc_relative(instr):
    def pcrel1_semantic(self, ctx, ins):
        PickAny = PickAny + PickAny  # noqa

    semantic = instr.semantic
    if m := _search_ast(semantic, pcrel1_semantic):
        try:
            # regn0 = m.picks[0].slice.attr
            # grpn0 = m.picks[0].value.attr
            # print(regn0, grpn0, instr.isa._ctx.GPR)
            # is_pc0 = eval(f'instr.isa._ctx.{grpn0}.get_obj("{regn0}").is_pc')
            regn1 = m.picks[1].attr
            grpn1 = m.picks[1].value.attr
            is_pc1 = eval(f'instr.isa._ctx.{grpn1}.get_obj("{regn1}").is_pc')
        except Exception:
            is_pc1 = False
        if is_pc1:
            return ast.unparse(m.picks[2])
    return None


def may_save_pc(instr):
    def savepc_semantic(self, ctx, ins):
        PickAny = PickAny + PickAny  # noqa

    semantic = instr.semantic
    if m := _search_ast(semantic, savepc_semantic):
        try:
            regn0 = m.picks[0].slice.attr
            grpn0 = m.picks[0].value.attr
            is_gpr0 = grpn0 in [grp.label for grp in instr.isa.registers]
            regn1 = m.picks[1].attr
            grpn1 = m.picks[1].value.attr
            is_pc1 = eval(f'instr.isa._ctx.{grpn1}.get_obj("{regn1}").is_pc')
            immv2 = m.picks[2].value
            is_imm2 = isinstance(immv2, int)
        except Exception:
            is_gpr0 = False
            is_pc1 = False
            is_imm2 = False
        if is_gpr0 and is_pc1 and is_imm2:
            return (regn0, grpn0, immv2)
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


def estimate_jump_ops(isa):
    zero = isa.abi.zero_reg
    # ra = isa.abi.ra_reg
    instrs = []
    for instr in isa.instructions:
        if type(instr.is_jump) is bool and instr.is_jump:
            if type(instr.is_indirect) is bool and not instr.is_indirect:
                instrs.append((instr, False))  # jump
            elif type(instr.is_indirect) is bool and instr.is_indirect:
                instrs.append((instr, True))  # jumpind
    for instr in isa.instructions:
        # if m := may_save_pc(instr):
        #     print(m)
        #     continue
        # print("JUMP?:", instr.__name__)
        if may_change_pc_absolute(instr):
            if (instr, True) not in instrs:
                instrs.append((instr, True))  # jumpind
        elif may_change_pc_relative(instr):
            if may_branch(instr.semantic) or may_ubranch(instr.semantic):
                continue
            if may_compare_branch(instr.semantic):
                continue
            if (instr, False) not in instrs:
                instrs.append((instr, False))  # jump
    def imm_width(x):
        instr, is_indirect = x
        for param in instr.params.inputs.values():
            if isa.is_imm_type(param.type_):
                prmobj = isa.get_param_obj(param.label, instr)
                return prmobj.width
        return sys.maxsize
    instrs.sort(key=imm_width, reverse=True)
    jump_ops = {"jump": [], "jumpind": []}
    for instr, is_indirect in instrs:
        operands = []
        for asm in instr.asm.ast:
            if asm[0] == '$' and asm != '$opn':
                label = asm[1:]
                prmobj = isa.get_param_obj(label, instr)
                if label in instr.params.outputs:
                    if isa.is_reg_type(instr.params.outputs[label].type_):
                        operands.append((prmobj, zero))
                    else:
                        operands.append((prmobj, 0))
                elif label in instr.params.inputs:
                    if is_indirect:
                        if isa.is_reg_type(instr.params.inputs[label].type_):
                            operands.append((prmobj, label))
                        else:
                            operands.append((prmobj, 0))
                    else:
                        if isa.is_reg_type(instr.params.inputs[label].type_):
                            operands.append((prmobj, zero))
                        else:
                            operands.append((prmobj, label))
        key = "jumpind" if is_indirect else "jump"
        jump_ops[key].append((instr, operands))
    return jump_ops


def estimate_call_ops(isa):
    zero = isa.abi.zero_reg
    ra = isa.abi.ra_reg
    instrs = []
    tail_instrs = []
    for instr in isa.instructions:
        if type(instr.is_call) is bool and instr.is_call:
            if type(instr.is_indirect) is bool and not instr.is_indirect:
                instrs.append((instr, False))  # call
            elif type(instr.is_indirect) is bool and instr.is_indirect:
                instrs.append((instr, True))  # callind
        if type(instr.is_tail) is bool and instr.is_tail:
            if type(instr.is_indirect) is bool and not instr.is_indirect:
                tail_instrs.append((instr, False))  # tail
            elif type(instr.is_indirect) is bool and instr.is_indirect:
                tail_instrs.append((instr, True))  # tailind
    longcall_s = []
    for alias in isa.instruction_aliases:
        if hasattr(alias, "is_call") and alias.is_call:
            asms = alias.dst
            opns = [re.split(r"\s*,?\s+", asm)[0] for asm in asms]
            # instrs_ = [next(filter(lambda x: x.opn == opn, isa.instructions), None) for opn in opns]
            instrs_ = []
            for opn in opns:
                instr = next(filter(lambda x: x.opn == opn, isa.instructions), None)
                is_indirect = False
                instrs_.append((instr, is_indirect))
            longcall_info = []
            for instr, is_indirect in instrs_:
                operands = []
                for asm in instr.asm.ast:
                    if asm[0] == '$' and asm != '$opn':
                        label = asm[1:]
                        prmobj = isa.get_param_obj(label, instr)
                        if label in instr.params.outputs:
                            if isa.is_reg_type(instr.params.outputs[label].type_):
                                operands.append((prmobj, ra))
                        elif label in instr.params.inputs:
                            if is_indirect:
                                if isa.is_reg_type(instr.params.inputs[label].type_):
                                    operands.append((prmobj, label))
                                else:
                                    operands.append((prmobj, 0))
                            else:
                                if isa.is_reg_type(instr.params.inputs[label].type_):
                                    # operands.append((prmobj, zero))
                                    operands.append((prmobj, ra))
                                else:
                                    operands.append((prmobj, label))
                longcall_info.append((instr, operands))
            if len(instrs_) > 1:
                longcall_s.append(longcall_info)
            else:
                pass
    longtail_s = []
    for alias in isa.instruction_aliases:
        if hasattr(alias, "is_tail") and alias.is_tail:
            asms = alias.dst
            opns = [re.split(r"\s*,?\s+", asm)[0] for asm in asms]
            opss = [re.split(r"\s*,?\s+", asm) for asm in asms]
            instrs_ = []
            for opn in opns:
                instr = next(filter(lambda x: x.opn == opn, isa.instructions), None)
                is_indirect = False
                instrs_.append((instr, is_indirect))
            longtail_info = []
            for iidx, (instr, is_indirect) in enumerate(instrs_):
                operands = []
                aidx = 1
                for asm in instr.asm.ast:
                    if asm[0] == '$' and asm != '$opn':
                        label = asm[1:]
                        alias_label = opss[iidx][aidx]
                        prmobj = isa.get_param_obj(label, instr)
                        if label in instr.params.outputs:
                            if isa.is_reg_type(instr.params.outputs[label].type_):
                                operands.append((prmobj, alias_label))
                        elif label in instr.params.inputs:
                            if is_indirect:
                                if isa.is_reg_type(instr.params.inputs[label].type_):
                                    operands.append((prmobj, alias_label))
                                else:
                                    operands.append((prmobj, 0))
                            else:
                                if isa.is_reg_type(instr.params.inputs[label].type_):
                                    operands.append((prmobj, alias_label))
                                else:
                                    operands.append((prmobj, label))
                        aidx += 1
                longtail_info.append((instr, operands))
            if len(instrs_) > 1:
                longtail_s.append(longtail_info)
            else:
                pass

    for instr in isa.instructions:
        if m := may_save_pc(instr):
            pass
        else:
            continue
        if m := may_change_pc_absolute(instr):
            tgtast = ast.parse(m)
            tgtast = resolve_unknown_variable(tgtast, instr.semantic)
            if type(tgtast) is ast.BinOp:
                pc_change_reg = tgtast.left
            else:
                pc_change_reg = tgtast
            # pc_change_regname = pc_change_reg.slice.attr
            pc_change_reggrp = pc_change_reg.value.attr
            if pc_change_reggrp == ra.group.label:
                if (instr, True) not in instrs:
                    instrs.append((instr, True))  # callind
                if (instr, True) not in tail_instrs:
                    tail_instrs.append((instr, True))
        elif m := may_change_pc_relative(instr):
            if may_branch(instr.semantic) or may_ubranch(instr.semantic):
                continue
            if may_compare_branch(instr.semantic):
                continue
            if (instr, False) not in instrs:
                instrs.append((instr, False))  # call
            if (instr, False) not in tail_instrs:
                tail_instrs.append((instr, False))
    def imm_width(x):
        instr, is_indirect = x
        for param in instr.params.inputs.values():
            if isa.is_imm_type(param.type_):
                prmobj = isa.get_param_obj(param.label, instr)
                return prmobj.width
        return sys.maxsize
    instrs.sort(key=imm_width, reverse=True)
    tail_instrs.sort(key=imm_width, reverse=True)
    call_ops = {"call": [], "callind": [], "longcall": [],
                "tail": [], "tailind": [], "longtail": []}
    for instr, is_indirect in instrs:
        operands = []
        for asm in instr.asm.ast:
            if asm[0] == '$' and asm != '$opn':
                label = asm[1:]
                prmobj = isa.get_param_obj(label, instr)
                if label in instr.params.outputs:
                    if isa.is_reg_type(instr.params.outputs[label].type_):
                        operands.append((prmobj, ra))
                elif label in instr.params.inputs:
                    if is_indirect:
                        if isa.is_reg_type(instr.params.inputs[label].type_):
                            operands.append((prmobj, label))
                        else:
                            operands.append((prmobj, 0))
                    else:
                        if isa.is_reg_type(instr.params.inputs[label].type_):
                            operands.append((prmobj, zero))
                        else:
                            operands.append((prmobj, label))
        key = "callind" if is_indirect else "call"
        call_ops[key].append((instr, operands))
    call_ops["longcall"] = longcall_s
    for tail_instr, is_indirect in tail_instrs:
        operands = []
        for asm in instr.asm.ast:
            if asm[0] == '$' and asm != '$opn':
                label = asm[1:]
                prmobj = isa.get_param_obj(label, instr)
                if label in instr.params.outputs:
                    if isa.is_reg_type(instr.params.outputs[label].type_):
                        operands.append((prmobj, zero))  # [TODO] alt_ra
                elif label in instr.params.inputs:
                    if is_indirect:
                        if isa.is_reg_type(instr.params.inputs[label].type_):
                            operands.append((prmobj, label))
                        else:
                            operands.append((prmobj, 0))
                    else:
                        if isa.is_reg_type(instr.params.inputs[label].type_):
                            operands.append((prmobj, zero))
                        else:
                            operands.append((prmobj, label))
        key = "tailind" if is_indirect else "tail"
        call_ops[key].append((instr, operands))
    call_ops["longtail"] = longtail_s
    return call_ops


def estimate_ret_ops(isa):
    zero = isa.abi.zero_reg
    ra = isa.abi.ra_reg
    instrs = []
    for instr in isa.instructions:
        if type(instr.is_return) is bool and instr.is_return:
            instrs.append(instr)
    for instr in isa.instructions:
        if m := may_change_pc_absolute(instr):
            tgtast = ast.parse(m)
            tgtast = resolve_unknown_variable(tgtast, instr.semantic)
            if type(tgtast) is ast.BinOp:
                pc_change_reg = tgtast.left
            else:
                pc_change_reg = tgtast
            # pc_change_regname = pc_change_reg.slice.attr
            pc_change_reggrp = pc_change_reg.value.attr
            if pc_change_reggrp == ra.group.label and instr not in instrs:
                instrs.append(instr)
    ret_ops = []
    for instr in instrs:
        ra_matched = False
        operands = []
        for asm in instr.asm.ast:
            if asm[0] == '$' and asm != '$opn':
                label = asm[1:]
                prmobj = isa.get_param_obj(label, instr)
                if label in instr.params.outputs and isinstance(prmobj, type(zero.group)):
                    operands.append((prmobj, zero))
                elif label in instr.params.inputs:
                    if isinstance(prmobj, type(ra.group)):
                        if not ra_matched:
                            operands.append((prmobj, ra))
                        else:
                            operands.append((prmobj, zero))
                    else:
                        operands.append((prmobj, 0))
        ret_ops.append((instr, operands))
    return ret_ops


def unsigned():
    pass


def get_alu_dag(semantic):
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
            if not rhs_l_unsigned:
                # dag_op = "mulhu"  # not correct
                # dag_op = "mulhsu"  # unknown IR operator
                dag_op = "mulhs"  # not correct
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
    li32_s = []
    li_s = []
    lui_s = []
    addi_s = []
    add_s = []
    for instr in isa.instructions:
        if m := may_load_immediate(instr.semantic):
            # r_tp = instr.params.inputs["imm"].type_
            imm_key = get_ast_name(m.picks[0])
            r_tp = instr.params.inputs[imm_key].type_
            imm = next(filter(lambda im: im.label == r_tp, isa.immediates), None)
            if imm.offset == 0:
                li_s.append((instr, imm))
                if imm.width == 32:
                    li32_s.append((instr, imm))
            else:
                lui_s.append((instr, imm))
            continue
        dag = get_alu_dag(instr.semantic)
        if dag:
            (op, (dst_name, dst_tp), (l_name, l_tp, l_u), (r_name, r_tp, r_u)) = dag
            # if op == "add" and r_name == "imm":
            if op == "add":
                if r_tp == "UnknownImm":
                    r_tp = instr.params.inputs[r_name].type_
                    imm = next(filter(lambda im: im.label == r_tp, isa.immediates), None)
                    addi_s.append((instr, imm))
                else:
                    add_s.append((instr, None))
    lui_addi_s = []
    for (lui, lui_imm) in lui_s:
        for (addi, addi_imm) in addi_s:
            # if lui_imm.offset == addi_imm.width:
            if lui_imm.offset >= addi_imm.width:
                lui_addi_s.append(((lui, lui_imm), (addi, addi_imm)))
                if lui_imm.offset == addi_imm.width and lui_imm.width + lui_imm.offset == 32:
                    li32_s.append(((lui, lui_imm), (addi, addi_imm)))
    li_ops = (li32_s, tuple(li_s), tuple(lui_s), tuple(addi_s), tuple(lui_addi_s), tuple(add_s))
    return li_ops


def is_lui_like(instr, lui_s):
    imm_types = []
    for key, value in instr.prm.inputs.items():
        if instr.isa.is_imm_type(value):
            imm_types.append(value)
    lui_imm_types = [info[1].label for info in lui_s]
    return imm_types == lui_imm_types


def may_compare(semantic):
    def compare(lhs, rhs):
        pass
    def cmp_semantic(s, ctx, ins):
        PickAny = compare(Any, Any)

    m = _match_ast(semantic, cmp_semantic)
    return m


cmp_br_funcs = (
    'compare_eq', 'compare_ne', 'compare_gt', 'compare_lt', 'compare_ge', 'compare_le',
    'compare_ueq', 'compare_une', 'compare_ugt', 'compare_ult', 'compare_uge', 'compare_ule',
)


def may_compare_branch(semantic):
    def cmp_br_semantic(s, ctx, ins):
        cond = PickAny(PickAny)

    m = _search_ast(semantic, cmp_br_semantic)
    if m and m.picks[0].id not in cmp_br_funcs:
        return None
        # new_picks = tuple([m.picks[0].id] + m.picks[1:])
        # m.picks = new_picks
    return m


def estimate_compare_branch_ops(isa):
    cmp_s = []
    cmp_br_s = {}
    for cmp_func in cmp_br_funcs:
        cmp_br_s.setdefault(cmp_func, list())
    for instr in isa.instructions:
        if m := may_compare_branch(instr.semantic):
            cmp_func = m.picks[0].id
            if type(m.picks[1]) is ast.Subscript:
                grp = m.picks[1].value.attr
                reg = m.picks[1].slice.value
            else:
                grp = m.picks[1].value.attr
                reg = m.picks[1].attr
            cmp_br_s[cmp_func].append((instr, grp, reg))
        elif m := may_compare(instr.semantic):
            if type(m.picks[0]) is ast.Subscript:
                grp = m.picks[0].value.attr
                reg = m.picks[0].slice.value
            else:
                grp = m.picks[0].value.attr
                reg = m.picks[0].attr
            cmp_s.append((instr, grp, reg))
    return (cmp_s, cmp_br_s)


def may_branch(semantic):
    def cmp_br_semantic(s, ctx, ins):
        cond = PickAny != PickAny

    m = _match_ast(semantic, cmp_br_semantic)
    return m


def may_ubranch(semantic):
    def cmp_ubr_semantic(s, ctx, ins):
        cond = unsigned(Any, PickAny) != unsigned(Any, PickAny)

    m = _match_ast(semantic, cmp_ubr_semantic)
    return m


br_ast = {
    ast.Eq: "eq",
    ast.NotEq: "ne",
    ast.Gt: "gt",
    ast.Lt: "lt",
    ast.GtE: "ge",
    ast.LtE: "le",
}
ubr_ast = {
    ast.Eq: "ueq",
    ast.NotEq: "une",
    ast.Gt: "ugt",
    ast.Lt: "ult",
    ast.GtE: "uge",
    ast.LtE: "ule",
}


def estimate_branch_ops(isa):
    br_s = {}
    for name in list(br_ast.values()) + list(ubr_ast.values()):
        br_s.setdefault(name, list())
    for instr in isa.instructions:
        m1 = may_branch(instr.semantic)
        m2 = may_ubranch(instr.semantic)
        if m1 or m2:
            m = m2 or m1
            is_unsigned = m == m2
            binop = type(m.picks[1])
            if type(m.picks[0]) is ast.Subscript:
                lgrp = m.picks[0].value.attr
                lreg = m.picks[0].slice.attr
            else:
                lgrp = m.picks[0].value.attr
                lreg = m.picks[0].attr
            if type(m.picks[2]) is ast.Subscript:
                rgrp = m.picks[2].value.attr
                rreg = m.picks[2].slice.attr
            elif type(m.picks[2]) is ast.Constant:
                rgrp = None
                rreg = m.picks[2].value
            else:
                rgrp = m.picks[2].value.attr
                rreg = m.picks[2].attr
            if is_unsigned:
                br_s[ubr_ast[binop]].append((instr, lgrp, lreg, rgrp, rreg))
            else:
                br_s[br_ast[binop]].append((instr, lgrp, lreg, rgrp, rreg))
    return br_s


def may_setcc(semantic):
    def setcc_semantic(s, ctx, ins):
        PickAny = PickAny != PickAny

    m = _match_ast(semantic, setcc_semantic)
    if m and type(m.picks[0]) is ast.Name and m.picks[0].id == 'cond':
        return None
    return m


def may_usetcc(semantic):
    def usetcc_semantic(s, ctx, ins):
        PickAny = unsigned(Any, PickAny) != unsigned(Any, PickAny)

    m = _match_ast(semantic, usetcc_semantic)
    if m and type(m.picks[0]) is ast.Name and m.picks[0].id == 'cond':
        return None
    return m


def estimate_setcc_ops(isa):
    setcc_s = {}
    for name in list(br_ast.values()) + list(ubr_ast.values()):
        setcc_s.setdefault(name, list())
    for instr in isa.instructions:
        m1 = may_setcc(instr.semantic)
        m2 = may_usetcc(instr.semantic)
        if m1 or m2:
            m = m2 or m1
            is_unsigned = m == m2
            binop = type(m.picks[2])
            if type(m.picks[0]) is ast.Subscript:
                dgrp = m.picks[0].value.attr
                dreg = m.picks[0].slice.attr
            else:
                lgrp = m.picks[1].value.attr
                lreg = m.picks[1].attr
            if type(m.picks[1]) is ast.Subscript:
                lgrp = m.picks[1].value.attr
                lreg = m.picks[1].slice.attr
            else:
                lgrp = m.picks[1].value.attr
                lreg = m.picks[1].attr
            if type(m.picks[3]) is ast.Subscript:
                rgrp = m.picks[3].value.attr
                rreg = m.picks[3].slice.attr
            elif type(m.picks[3]) is ast.Constant:
                rgrp = None
                rreg = m.picks[3].value
            elif type(m.picks[3]) is ast.Attribute:  # ins.imm
                rgrp = "UnknownImm"
                rreg = m.picks[3].attr
            else:
                rgrp = m.picks[3].value.attr
                rreg = m.picks[3].attr
            if is_unsigned:
                setcc_s[ubr_ast[binop]].append((instr, dgrp, dreg, lgrp, lreg, rgrp, rreg))
            else:
                setcc_s[br_ast[binop]].append((instr, dgrp, dreg, lgrp, lreg, rgrp, rreg))
    return setcc_s


def may_load(isa, semantic):
    def load_semantic(s, ctx, ins):
        PickAny = ctx.PickAny.read(PickAny, PickAny)

    m = _search_ast(semantic, load_semantic)
    return m


def may_uload(isa, semantic):
    def uload_semantic(s, ctx, ins):
        PickAny = unsigned(Any, ctx.PickAny.read(PickAny, PickAny))

    m = _search_ast(semantic, uload_semantic)
    if may_compare_branch(semantic):
        return None
    return m

load_table = {
    "8": "load8",
    "16": "load16",
    "32": "load32",
}
uload_table = {
    "8": "uload8",
    "16": "uload16",
    "32": "uload32",
}

def estimate_load_ops(isa):
    load_ops = {}
    for key in list(load_table.values()) + list(uload_table.values()):
        load_ops[key] = list()
    for instr in isa.instructions:
        m1 = may_load(isa, instr.semantic)
        m2 = may_uload(isa, instr.semantic)
        if m1 or m2:
            m = m2 or m1
            is_unsigned = m == m2
            mem = m.picks[1]
            memobj = None
            for mo in isa.memories:
                if mem.attr in mo.label:
                    memobj = mo
                    break
            else:
                continue
            bitwidth = m.picks[2].value
            addr_ast = ast.parse(m.picks[3])
            addr_ast = resolve_unknown_variable(addr_ast, instr.semantic)
            if type(addr_ast) is ast.BinOp:
                # addr = reg + imm
                reg_name = addr_ast.left.slice.attr
                imm_name = addr_ast.right.attr
            else:
                # addr = reg
                reg_name = addr_ast.slice.attr
                imm_name = None
            addrinfo = (reg_name, imm_name)
            dst_ast = ast.parse(m.picks[0])
            dst_name = dst_ast.slice.attr
            if is_unsigned:
                key = uload_table[str(bitwidth)]
            else:
                key = load_table[str(bitwidth)]
            load_ops[key].append((instr, dst_name, memobj, bitwidth, addrinfo))
    return load_ops


def may_store(isa, semantic):
    def store_semantic(s, ctx, ins):
        ctx.PickAny.write(PickAny, PickAny, PickAny)

    m = _search_ast(semantic, store_semantic)
    return m

store_table = {
    "8": "store8",
    "16": "store16",
    "32": "store32",
}

def estimate_store_ops(isa):
    store_ops = {}
    for key in list(store_table.values()):
        store_ops[key] = list()
    for instr in isa.instructions:
        if m := may_store(isa, instr.semantic):
            mem = m.picks[0]
            memobj = None
            for mo in isa.memories:
                if mem.attr in mo.label:
                    memobj = mo
                    break
            else:
                continue
            bitwidth = m.picks[1].value
            addr_ast = ast.parse(m.picks[2])
            addr_ast = resolve_unknown_variable(addr_ast, instr.semantic)
            if type(addr_ast) is ast.BinOp:
                # addr = reg + imm
                reg_name = addr_ast.left.slice.attr
                imm_name = addr_ast.right.attr
            else:
                # addr = reg
                reg_name = addr_ast.slice.attr
                imm_name = None
            addrinfo = (reg_name, imm_name)
            src_ast = ast.parse(m.picks[3])
            src_name = src_ast.slice.attr
            key = store_table[str(bitwidth)]
            store_ops[key].append((instr, src_name, memobj, bitwidth, addrinfo))
    return store_ops
