import os
import re
import glob
from jinja2 import Template
from isana.semantic import (
    may_change_pc_absolute,
    may_change_pc_relative,
    may_use_pc_relative,
    may_take_memory_address,
    get_alu_dag,
    estimate_jump_ops,
    estimate_call_ops,
    estimate_ret_ops,
    estimate_load_immediate_ops,
    is_lui_like,
    estimate_compare_branch_ops,
    estimate_branch_ops,
    estimate_setcc_ops,
    estimate_load_ops,
    estimate_store_ops,
)
from isana.isa import (
    Immediate,
    InstructionAlias, PseudoInstruction,
)


_default_target = "Xpu"
_default_triple = "xpu-unknown-elf"


class KwargsClass():
    keys = ()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class RegisterBase(KwargsClass):
    keys = (
        'name',
        'bitsize',
    )


class RegisterDef(KwargsClass):
    keys = (
        'varname',
        'basename',
        'no',
        'name',
        'has_aliases',
        'aliases',
        'dwarfno',
    )

class RegisterClassDef(KwargsClass):
    keys = (
        'varname',
        'regs',
        'reg_varnames',
        'bitsize',
    )


class RegisterInfo(KwargsClass):
    keys = (
        'RA',
        'SP',
        'FP',
    )

class AsmOperandCls(KwargsClass):
    keys = (
        'name',
        'enums',
    )

class OperandCls(KwargsClass):
    keys = (
        'varname',
        'basecls',
    )

class OperandType(KwargsClass):
    keys = (
        'varname',
        'basecls',
        'cond',
    )

class BrImmOperandAttr(KwargsClass):
    keys = (
        'width',
        'offset',
    )

class InstrDefs(KwargsClass):
    keys = (
        'varname',
        'outs',
        'ins',
        'asmstr',
        'pattern',
        'params',
        'bit_defs',
        'bit_insts',
        'attrs',
    )


instr_attr_table = {
    'is_return': ("isReturn", "isTerminator"),
    'is_jump': ("isBranch", "isTerminator"),
    'is_branch': ("isBranch", "isTerminator"),
    'is_indirect': ("isIndirectBranch", "isTerminator"),
    # '': "isCompare",
    # '': "isMoveImm",
    # '': "isMoveReg",
    # '': "isBitcast",
    # '': "isSelect",
    # '': "isBarrier",
    'is_call': ("isCall", "isBarrier"),
    # '': "isAdd",
    # '': "isTrap",
    'is_load': "mayLoad",
    'is_pop': "mayLoad",
    'is_store': "mayStore",
    'is_push': "mayStore",
    # '': "isTerminator",
}


class Fixup(KwargsClass):
    keys = (
        'target',
        'number',
        'name_enum',
        'addend',
        'bin',
        'offset',
        'size',
        'flags',
        'reloc_procs',
        'val_carryed',
        'is_pcrel',
    )

    def __init__(self, **kwargs):
        self.target = kwargs.pop('target', _default_target)
        self.number = kwargs.pop('number', -1)
        self.name = kwargs.pop('name', str())
        self.addend = kwargs.pop('addend', None)
        self.bin = kwargs.pop('bin', None)
        self.name_enum = f"fixup_{self.target.lower()}_{self.name}"
        self.reloc_procs = list()
        self.val_carryed = str()
        self.is_pcrel = False
        super().__init__(**kwargs)


def auto_make_fixups(isa, li_ops, call_ops):
    fixups = list()
    fixups += auto_make_relocations(isa, li_ops, call_ops)
    return fixups


def auto_make_relocations(isa, li_ops, call_ops):
    (li32, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops

    relocs = {
        "pc_abs": list(),
        "pc_rel": list(),
        "pc_use": list(),
        "mem_addr": list(),
        "other_imm": list(),
    }
    instrs = dict()
    for instr in isa.instructions:
        if not hasattr(instr, 'semantic'):
            continue
        bin_filtered = re.sub(r"\$(?!opc|imm)\w+", r"$_", str(instr.bin))
        relocinfo = (instr.bin.bitsize, bin_filtered)
        if may_change_pc_absolute(instr):
            key = "pc_abs"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(instr)
        elif may_change_pc_relative(instr):
            key = "pc_rel"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(instr)
        elif may_use_pc_relative(instr):
            key = "pc_use"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(instr)
        elif may_take_memory_address(instr.semantic):
            key = "mem_addr"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(instr)
        elif "imm" in instr.prm.inputs.keys():  # TODO fix condition
            key = "other_imm"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(instr)
        else:
            pass
    fixups = list()
    fixups += [
        Fixup(name="32", offset=0, size=32, flags=0, bin=32),
        Fixup(name="64", offset=0, size=64, flags=0, bin=64),
        Fixup(name="call", offset=0, size=64, flags=0, bin=64),
    ]
    for key in relocs:
        relocs[key] = sorted(list(set(relocs[key])), key=lambda x: str(x[1]))
        for ri, info in enumerate(relocs[key]):
            bitsize, bin_ = info
            fixup = Fixup()
            fixup.name = f"{key}_{ri}"
            fixup.offset = 0
            fixup.size = bitsize  # TODO: fix it
            if key in ("pc_rel", "pc_use"):
                fixup.flags = "MCFixupKindInfo::FKF_IsPCRel"
                fixup.is_pcrel = True
            else:
                fixup.flags = "0"  # TODO: fix it
            fixup.bin = bin_
            fixup.instrs = [i for i in sorted(list(set(instrs[(key, bin_)])), key=lambda x: x.opn)]
            fixups.append(fixup)

    instr_reloc_table = dict()
    for fixup in fixups:
        if hasattr(fixup, "instrs"):
            for instr in fixup.instrs:
                instr_reloc_table[instr] = fixup

    lui_op, lui_imm = lui_s[0]
    for fixup in fixups:
        procs = list()
        if fixup.bin is None:
            raise Exception("fixup must have bins: {}".format(fixup.name))
        if fixup.name == "call":
            pass
        elif isinstance(fixup.bin, int):
            procs.append("  | val")
        else:
            # get symbol imm type
            val_carryed = "val"
            if "imm" in fixup.instrs[0].prm.inputs:
                is_lui = False
                for instr in fixup.instrs:
                    if instr in [op[0] for op in lui_s]:
                        is_lui = True
                        immobj = isa.get_param_obj("imm", instr)
                if is_lui and immobj.offset > 0:
                    val_carryed = "((val + {}) & ~{})".format(
                        2 ** (immobj.offset - 1),
                        2 ** immobj.offset - 1,
                    )
            fixup.val_carryed = val_carryed

            bit_sum = 0
            for bits in reversed(fixup.instrs[0].bin.bitss):
                if bits.label == "$imm":
                    procs.append("  | (((val >> {}) & {}) << {})".format(
                        bits.lsb,
                        2 ** bits.size() - 1,
                        bit_sum,
                    ))
                bit_sum += bits.size()
        fixup.reloc_procs = procs
    for fixup in fixups:
        if fixup.name == "call":
            procs = list()
            if call_ops["longcall"]:
                ops = call_ops["longcall"][0]
                pos_sum = 0
                fixup.instrs = [op for op, oprands in ops]
                for op_info in ops:
                    op, operands = op_info
                    val_carryed = "val"
                    if is_lui_like(op, lui_s):
                        if may_use_pc_relative(op):
                            fixup.flags = "MCFixupKindInfo::FKF_IsPCRel"
                            fixup.is_pcrel = True
                        immobj = isa.get_param_obj("imm", op)
                        val_carryed = "((val + {}) & ~{})".format(
                            2 ** (immobj.offset - 1),
                            2 ** immobj.offset - 1,
                        )
                    bit_sum = 0
                    procs.append("| ((0 // {}".format(op.opn))
                    for bits in reversed(op.bin.bitss):
                        if bits.label == "$imm":
                            procs.append("  | ((({val} >> {}) & {}) << {})".format(
                                bits.lsb,
                                2 ** bits.size() - 1,
                                bit_sum,
                                val=val_carryed,
                            ))
                        bit_sum += bits.size()
                    procs.append(") << {})".format(pos_sum))
                    pos_sum += op.bin.bitsize
            else:
                op, operands = call_ops["call"][0]
                fixup.instrs = [op]
                bit_sum = 0
                procs.append("  | val")
                for bits in reversed(op.bin.bitss):
                    if bits.label == "$imm":
                        procs.append("  | (((val >> {}) & {}) << {})".format(
                            bits.lsb,
                            2 ** bits.size() - 1,
                            bit_sum,
                        ))
                    bit_sum += bits.size()
            fixup.size = sum([instr.bin.bitsize for instr in fixup.instrs])
            fixup.reloc_procs = procs
    return fixups


def get_instr_pattern(instr):
    if ret := get_alu_dag(instr.semantic):
        (op, (dst_name, dst_tp), (l_name, l_tp, l_u), (r_name, r_tp, r_u)) = ret
        # TODO: fix to add convert function to unsigned operand
        if r_tp == "UnknownImm":
            r_tp = instr.params.inputs[r_name].type_
        s = "[(set {}, ({} {}, {}))]".format(
            "{}:${}".format(dst_tp, dst_name),
            op,  # get_basic_operator(instr.opn)
            "{}:${}".format(l_tp, l_name),
            "{}:${}".format(r_tp, r_name),
        )
        return s
    return "[]"


def get_instr_alias(alias, isa):
    if isinstance(alias, PseudoInstruction):
        return None
    if isinstance(alias, InstructionAlias):
        srcstr = alias.src
        dstnode = []
        alias_ops = re.split(r"\s*,?\s+", alias.dst[0])
        instr = next(filter(lambda x: x.opn == alias_ops[0], isa.instructions), None)
        if instr is None:
            return None
        instr = instr()
        instr.isa = isa
        instr.decode(instr.opc)  # dummy decode as all parameter is 0
        instr_ops = re.split(r"\s*,?\s+", instr.asm.pattern)
        dstnode.append(instr.__class__.__name__.upper())
        alias_ops = [op.strip("()")for op in alias_ops][1:]
        instr_ops = [op.strip("()")for op in instr_ops][1:]
        instr_op_labels = [op if op[0] != "$" else op[1:] for op in instr_ops]
        params = []
        for prm in list(instr.prm.outputs.keys()) + list(instr.prm.inputs.keys()):
            if prm not in params:
                params.append(prm)
        for i, prm in enumerate(params):
            idx = instr_op_labels.index(prm)
            if alias_ops[idx][0] == "$":
                label = alias_ops[idx][1:]
                prmobj = isa.get_param_obj(instr_ops[idx][1:], instr)
                cls = prmobj.label
                if isinstance(prmobj, Immediate):
                    if may_change_pc_relative(instr):
                        cls = "Br" + cls
                dstnode.append("{}:${}".format(cls, label))
            else:
                dstnode.append(alias_ops[idx].upper())
        return (srcstr, dstnode)
        # dstnode = "({} {})".format(dstnode[0], ", ".join(dstnode[1:]))
        # s = 'InstAlias<"{}", {}>'.format(srcstr, dstnode)
        # return s


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


def estimate_load_immediate_dag(isa, li_ops):
    (li32_s, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops
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
    for ops in lui_addi_s + li_s + lui_s + addi_s:
        if ops in lui_addi_s:
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
            if ops == li32_s[0]:
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


def estimate_branch_dag(isa, cmp_ops, br_ops, setcc_ops, zeroreg):
    # print(cmp_ops)
    # print(br_ops)
    # print(setcc_ops)
    dags = []
    # cmp + cmp_br
    if cmp_ops[0]:
        pass
    # setcc + br
    if br_ops and setcc_ops and zeroreg:
        if True:
            brop, ltp, lnm, rtp, rnm = br_ops['ne'][0]
            brtp = "Br" + list(brop.params.inputs.values())[-1].type_
            pat_in = '(brcond {cctp}:$cond, bb:$dst)'.format(
                cctp=ltp,
            )
            pat_out = '({brop} {cctp}:$cond, {zero}, {bb}:$dst)'.format(
                brop=br_ops['ne'][0][0].__name__.upper(),
                cctp=ltp,
                zero=zeroreg,
                bb=brtp,
            )
            pat = f'def : Pat<{pat_in}, {pat_out}>;'
            dags.append(pat)
        for condkey in ('eq', 'ne'):
            brop, ltp, lnm, rtp, rnm = br_ops[condkey][0]
            brtp = "Br" + list(brop.params.inputs.values())[-1].type_
            pat_in = '(brcond (i32 (set{cc} {lhstp}:$lhs, 0)), bb:$dst)'.format(
                cc=condkey,
                lhstp=ltp,
            )
            pat_out = '({brop} {lhstp}:$lhs, {zero}, {bb}:$dst)'.format(
                brop=br_ops[condkey][0][0].__name__.upper(),
                lhstp=ltp,
                zero=zeroreg,
                bb=brtp,
            )
            pat = f'def : Pat<{pat_in}, {pat_out}>;'
            dags.append(pat)
        for condkey in br_ops.keys():
            if condkey in ('eq', 'ueq', 'ne', 'une'):
                if condkey in ('eq', 'ueq'):
                    brkey = 'eq'
                else:
                    brkey = 'ne'
                brop, ltp, lnm, rtp, rnm = br_ops[brkey][0]
                brtp = "Br" + list(brop.params.inputs.values())[-1].type_
                pat_out = '({brop} {lhstp}:$lhs, {rhstp}:$rhs, {bb}:$dst)'.format(
                    brop=brop.__name__.upper(),
                    lhstp=ltp,
                    rhstp=rtp,
                    bb=brtp,
                )
            else:
                if condkey in ('gt', 'ugt', 'lt', 'ult'):
                    brkey = 'ne'
                else:
                    brkey = 'eq'
                brop, ltp, lnm, rtp, rnm = br_ops[brkey][0]
                brtp = "Br" + list(brop.params.inputs.values())[-1].type_
                if condkey in ('gt', 'lt', 'ge', 'le'):
                    setcckey = 'lt'
                else:
                    setcckey = 'ult'
                for v in setcc_ops[setcckey]:
                    setccop, dtp, dnm, ltp, lnm, rtp, rnm = v
                    if rtp != 'UnknownImm':
                        break
                if condkey in ('gt', 'ugt', 'le', 'ule'):
                    pat_out_fmtstr = '({brop} ({setccop} {rhstp}:$rhs, {lhstp}:$lhs), {zero}, {bb}:$dst)'
                else:
                    pat_out_fmtstr = '({brop} ({setccop} {lhstp}:$lhs, {rhstp}:$rhs), {zero}, {bb}:$dst)'
                pat_out = pat_out_fmtstr.format(
                    brop=brop.__name__.upper(),
                    setccop=setccop.__name__.upper(),
                    lhstp=ltp,
                    rhstp=rtp,
                    zero=zeroreg,
                    bb=brtp,
                )
            pat_in = '(brcond (i32 (set{cc} {lhstp}:$lhs, {rhstp}:$rhs)), bb:$dst)'.format(
                cc=condkey,
                lhstp=ltp,
                rhstp=rtp,
            )
            pat = f'def : Pat<{pat_in}, {pat_out}>;'
            dags.append(pat)

    return dags


def estimate_load_dag(isa, load_ops):
    def_load_dags = []
    pat_load_dags = []
    load_srcop_table = {
        "load8": ["sextloadi8 ", " extloadi8 "],
        "load16": ["sextloadi16", " extloadi16"],
        "load32": ["    load   "],
        # "load32": ["    load   ", "sextloadi32", " extloadi32"],  # 64bit support
        "uload8": ["zextloadi8 "],
        "uload16": ["zextloadi16"],
        "uload32": ["zextloadi32"],
    }
    for key, load_op_list in load_ops.items():
        if not load_op_list:
            continue
        load_op, dst_name, memobj, bitwidth, addrinfo = load_op_list[0]
        outs = []
        for label, param in load_op.params.outputs.items():
            out_ = "{}:$dst".format(param.type_)
            outs.append(out_)
        ins = []
        for label, param in load_op.params.inputs.items():
            if isa.is_reg_type(param.type_):
                ins.append("{}:$addr".format(param.type_))
            else:
                ins.append("Imm:$offset")
        s = 'def PseudoFI_{opname} : {{Xpu}}Inst<(outs {outs}), (ins {ins}), "", []>;'.format(
            opname=load_op.__name__.upper(),
            outs=', '.join(outs),
            ins=', '.join(ins),
        )
        def_load_dags.append(s)

        reg1_prmobj = isa.get_param_obj(addrinfo[0], load_op)
        for srcopname in load_srcop_table[key]:
            s = 'def : Pat<({srcopname} (AddrReg {reg1}:$rs1, Imm:$imm)), '.format(
                srcopname=srcopname,
                reg1=reg1_prmobj.label,
            )
            s += '({opname} {reg1}:$rs1, Imm:$imm)>;'.format(
                opname=load_op.__name__.upper(),
                reg1=reg1_prmobj.label,
            )
            pat_load_dags.append(s)
            s = 'def : Pat<({srcopname} (FIAddr  {reg1}:$rs1, Imm:$imm)), '.format(
                srcopname=srcopname,
                reg1=reg1_prmobj.label,
            )
            s += '(PseudoFI_{opname} {reg1}:$rs1, Imm:$imm)>;'.format(
                opname=load_op.__name__.upper(),
                reg1=reg1_prmobj.label,
            )
            pat_load_dags.append(s)
    return (def_load_dags, pat_load_dags)


def estimate_store_dag(isa, store_ops):
    def_store_dags = []
    pat_store_dags = []
    store_srcop_table = {
        "store8": ["truncstorei8 "],
        "store16": ["truncstorei16"],
        "store32": ["     store   "],
        # "store32": ["     store   ", "truncstorei32", " truncstorei32"],  # 64bit support
    }
    for key, store_op_list in store_ops.items():
        if not store_op_list:
            continue
        store_op, src_name, memobj, bitwidth, addrinfo = store_op_list[0]
        outs = []
        ins = []
        for label, param in store_op.params.inputs.items():
            if isa.is_reg_type(param.type_):
                if label == src_name:
                    ins.append("{}:${}".format(param.type_, label))
                else:
                    ins.append("{}:$addr".format(param.type_))
            else:
                ins.append("Imm:$offset")
        s = 'def PseudoFI_{opname} : {{Xpu}}Inst<(outs {outs}), (ins {ins}), "", []>;'.format(
            opname=store_op.__name__.upper(),
            outs=', '.join(outs),
            ins=', '.join(ins),
        )
        def_store_dags.append(s)

        reg2_prmobj = isa.get_param_obj(src_name, store_op)
        reg1_prmobj = isa.get_param_obj(addrinfo[0], store_op)
        for srcopname in store_srcop_table[key]:
            s = 'def : Pat<({srcopname} {reg2}:$rs2, (AddrReg {reg1}:$rs1, Imm:$imm)), '.format(
                srcopname=srcopname,
                reg2=reg2_prmobj.label,
                reg1=reg1_prmobj.label,
            )
            s += '({opname} {reg2}:$rs2, {reg1}:$rs1, Imm:$imm)>;'.format(
                opname=store_op.__name__.upper(),
                reg2=reg2_prmobj.label,
                reg1=reg1_prmobj.label,
            )
            pat_store_dags.append(s)
            s = 'def : Pat<({srcopname} {reg2}:$rs2, (FIAddr  {reg1}:$rs1, Imm:$imm)), '.format(
                srcopname=srcopname,
                reg2=reg2_prmobj.label,
                reg1=reg1_prmobj.label,
            )
            s += '(PseudoFI_{opname} {reg2}:$rs2, {reg1}:$rs1, Imm:$imm)>;'.format(
                opname=store_op.__name__.upper(),
                reg2=reg2_prmobj.label,
                reg1=reg1_prmobj.label,
            )
            pat_store_dags.append(s)
    return (def_store_dags, pat_store_dags)


def estimate_pseudo_jump_dag(isa, jump_ops):
    jump_op = jump_ops["jump"][0]
    jump_op, operands = jump_op
    s = jump_op.__name__.upper()
    s_ops = []
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):  # maybe 'imm'
            s_ops += ["{}:${}".format("Br" + prmobj.label, value)]
        elif isinstance(value, int):
            s_ops += [str(value)]
        else:
            s_ops += [value.label.upper()]
    s = s + " " + ', '.join(s_ops)
    return s


def estimate_pseudo_jumpind_dag(isa, jump_ops):
    jump_op = jump_ops["jumpind"][0]
    jump_op, operands = jump_op
    s = jump_op.__name__.upper()
    s_ops = []
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):
            s_ops += ["{}:${}".format(prmobj.label, value)]
        elif isinstance(value, int):
            s_ops += [str(value)]
        else:
            s_ops += [value.label.upper()]
    s = s + " " + ', '.join(s_ops)
    return s


def estimate_pseudo_ret_dag(isa, ret_ops):
    ret_op = ret_ops[0]
    ret_op, operands = ret_op
    s = ret_op.__name__.upper()
    s_ops = []
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):  # maybe 'imm'
            s_ops += ["{}:${}".format("Br" + prmobj.label, value)]
        elif isinstance(value, int):
            s_ops += [str(value)]
        else:
            s_ops += [value.label.upper()]
    s = s + " " + ', '.join(s_ops)
    return s


def estimate_pseudo_call_dag(isa, call_ops):
    call_op = call_ops["call"][0]
    call_op, operands = call_op
    s = call_op.__name__.upper()
    s_ops = []
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):  # maybe 'imm'
            # s_ops += ["call_symbol:$func"]
            s_ops += ["{}:$func".format("Br" + prmobj.label)]
        elif isinstance(value, int):
            s_ops += [str(value)]
        else:
            s_ops += [value.label.upper()]
    s = s + " " + ', '.join(s_ops)
    return s


def estimate_pseudo_call_asm(isa, call_ops):
    call_op = call_ops["call"][0]
    call_op, operands = call_op
    s = call_op.__name__
    s_ops = []
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):  # maybe 'imm'
            s_ops += ["$func"]
        elif isinstance(value, int):
            s_ops += [str(value)]
        else:
            s_ops += [value.label]
    s = s + " " + ', '.join(s_ops)
    return s


def estimate_pseudo_callind_dag(isa, call_ops):
    call_op = call_ops["callind"][0]
    call_op, operands = call_op
    s = call_op.__name__.upper()
    s_ops = []
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):
            s_ops += ["{}:${}".format(prmobj.label, value)]
        elif isinstance(value, int):
            s_ops += [str(value)]
        else:
            s_ops += [value.label.upper()]
    s = s + " " + ', '.join(s_ops)
    return s


def estimate_copy_reg_buildmi(isa, mv_ops, addi_ops, add_ops, zeroreg):
    for ops in mv_ops:
        return ""
    for ops in addi_ops:
        op, imm = ops
        opname = op.opn.upper()
        buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::{opname}), DstReg)"
        for param in op.params.inputs.values():
            if isa.is_reg_type(param.type_):
                buildmi += ".addReg(SrcReg, getKillRegState(KillSrc) | getRenamableRegState(RenamableSrc))"
            elif isa.is_imm_type(param.type_):
                buildmi += ".addImm(0)"
            else:
                buildmi += f"/*{param} {param.type_}*/ "
        buildmi += ";"
        return buildmi
    for ops in add_ops:
        op, imm = ops
        opname = op.opn.upper()
        buildmi = f"BuildMI(MBB, MBBI, DL, get({{Xpu}}::{opname}), DstReg)"
        for param in op.params.inputs.values():
            if isa.is_reg_type(param.type_):
                buildmi += ".addReg(SrcReg, getKillRegState(KillSrc) | getRenamableRegState(RenamableSrc))"
            elif isa.is_imm_type(param.type_):
                buildmi += f".addReg({{Xpu}}::{zeroreg})"
            else:
                buildmi += f"/*{param} {param.type_}*/ "
        buildmi += ";"
        return buildmi


def estimate_mc_expand_longcall_codes(isa, call_ops):
    sss = []
    if call_ops["longcall"]:
        for i, op_info in enumerate(call_ops["longcall"][0]):
            op, operands = op_info
            s = "TmpInst = MCInstBuilder({{Xpu}}::{opname})".format(
                opname=op.__name__.upper(),
            )
            for op in operands:
                prmobj, value = op
                if isinstance(value, str):  # maybe 'imm'
                    if i == 0:
                        s += ".addExpr(CallExpr)"
                    else:
                        s += ".addImm(0)"
                elif isinstance(value, int):
                    s += ".addImm({})".format(value)
                else:
                    s += ".addReg({{Xpu}}::{})".format(value.label.upper())
            s += ";"

            ss = [
                s,
                "Binary = getBinaryCodeForInstr(TmpInst, Fixups, STI);",
                "support::endian::write(CB, Binary, llvm::endianness::little);",
            ]
            sss += ss
    return sss


def estimate_mc_expand_call_codes(isa, call_ops):
    call_op, operands = call_ops["call"][0]
    s = "TmpInst = MCInstBuilder({{Xpu}}::{opname})".format(
        opname=call_op.__name__.upper(),
    )
    for op in operands:
        prmobj, value = op
        if isinstance(value, str):  # maybe 'imm'
            s += ".addExpr(CallExpr)"
        elif isinstance(value, int):
            s += ".addImm({})".format(value)
        else:
            s += ".addReg({{Xpu}}::{})".format(value.label.upper())
    s += ";"

    ss = [
        s,
        "Binary = getBinaryCodeForInstr(TmpInst, Fixups, STI);",
        "support::endian::write(CB, Binary, llvm::endianness::little);",
    ]
    return ss


def estimate_add_immediate_codes(isa, li_ops):
    def get_cond(imm):
        cond = "!(Amount & {mask}) && ({minv} <= (Amount>>{shift})) && ((Amount>>{shift}) <= {maxv})".format(
            mask=int(pow(2, imm.offset) - 1),
            shift=imm.offset,
            minv=-int(pow(2, imm.width)),
            maxv=int(pow(2, imm.width) - 1),
        )
        return cond

    (li32_s, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops
    codes = list()
    for ops in li_s + lui_s + addi_s + lui_addi_s:
        vardefs = []
        buildmis = []
        if ops in lui_addi_s:
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
                s = "((Amount + {half}) >> {shift}) & {mask}".format(
                    half=2 ** (lui_imm.offset - 1),
                    shift=lui_imm.offset,
                    mask=2 ** lui_imm.width - 1,
                )
            else:
                s = "((Amount >> {shift})) & {mask}".format(
                    shift=lui_imm.offset,
                    mask=2 ** lui_imm.width - 1,
                )
            if hasattr(lui_imm, "signed"):
                s = "SignExtend64<{width}>({s})".format(
                    width=lui_imm.width,
                    s=s,
                )
            vardef = "int64_t Hi = {};".format(s)
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
            s = "Amount & {mask}".format(mask=2 ** addi_imm.width - 1)
            if hasattr(addi_imm, "signed"):
                s = "SignExtend64<{width}>({s})".format(width=addi_imm.width, s=s)
            vardef = "int64_t Lo = {};".format(s)
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
        elif ops in li_s or ops in lui_s:
            op, imm = ops
            cond = get_cond(imm)
            cond = f"if (/*{imm.label}*/ {cond})"
            if len(codes) > 0:
                cond = "else " + cond
            opname = op.opn.upper()
            # l[u]i : l[u]i t, hi(amount); add dst, src, t
            vardef = "Register TempReg = MRI.createVirtualRegister(&{Xpu}::GPRRegClass);"
            vardefs.append(vardef)
            if ops in lui_s:
                s = "((Amount >> {shift})) & {mask}".format(
                    shift=imm.offset,
                    mask=2 ** imm.width - 1,
                )
                if hasattr(imm, "signed"):
                    s = "SignExtend64<{width}>({s})".format(
                        width=imm.width,
                        s=s,
                    )
                vardef = "int64_t Hi = {};".format(s)
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
            codes.append((cond, vardefs, buildmis))
        else:
            op, imm = ops
            cond = get_cond(imm)
            cond = f"if (/*{imm.label}*/ {cond})"
            if len(codes) > 0:
                cond = "else " + cond
            opname = op.opn.upper()
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
            # codes.append((cond, vardefs, buildmis))
    return codes


def estimate_selectaddr_codes(isa, li_ops, has_addr):
    def get_cond(imm):
        cond = "!(CVal & {mask}) && ({minv} <= (CVal>>{shift})) && ((CVal>>{shift}) <= {maxv})".format(
            mask=int(pow(2, imm.offset) - 1),
            shift=imm.offset,
            minv=-int(pow(2, imm.width)),
            maxv=int(pow(2, imm.width) - 1),
        )
        return cond

    (li32_s, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops
    codes = list()
    for ops in addi_s + lui_addi_s:
        vardefs = []
        sdvalues = []
        if isinstance(ops[0], tuple):
            lui_op, lui_imm = ops[0]
            addi_op, addi_imm = ops[1]
            cond = "else"
            if hasattr(addi_imm, "signed"):
                s = "((CVal + {half}) >> {shift}) & {mask}".format(
                    half=2 ** (lui_imm.offset - 1),
                    shift=lui_imm.offset,
                    mask=2 ** lui_imm.width - 1,
                )
            else:
                s = "((CVal >> {shift})) & {mask}".format(
                    shift=lui_imm.offset,
                    mask=2 ** lui_imm.width - 1,
                )
            if hasattr(lui_imm, "signed"):
                s = "SignExtend64<{width}>({s})".format(
                    width=lui_imm.width,
                    s=s,
                )
            vardef = "int64_t Hi = {};".format(s)
            vardefs.append(vardef)
            s = "CVal & {mask}".format(mask=2 ** addi_imm.width - 1)
            if hasattr(addi_imm, "signed"):
                s = "SignExtend64<{width}>({s})".format(width=addi_imm.width, s=s)
            vardef = "int64_t Lo = {};".format(s)
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


def estimate_getaddr_codes(isa, li_ops, phase):
    (li32_s, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops
    codes = list()
    for ops in addi_s + lui_addi_s:
        if phase == 'lla':
            pass
        elif phase == 'lga':
            pass
        elif phase == 'la':
            ops = lui_addi_s[0]
            lui_op, lui_imm = ops[0]
            addi_op, addi_imm = ops[1]
            codes = [
                "SDValue AddrHi = getTargetNode(N, DL, Ty, DAG, {{Xpu}}II::{mo_sym_hi});".format(
                    mo_sym_hi="MO_SYMBOL",
                ),
                "SDValue AddrLo = getTargetNode(N, DL, Ty, DAG, {{Xpu}}II::{mo_sym_lo});".format(
                    mo_sym_lo="MO_SYMBOL",
                ),
                "SDValue MNHi = SDValue(DAG.getMachineNode({{Xpu}}::{lui}, DL, Ty, AddrHi), 0);".format(
                    lui=lui_op.__name__.upper(),
                ),
                "return SDValue(DAG.getMachineNode({{Xpu}}::{addi}, DL, Ty, MNHi, AddrLo), 0);".format(
                    addi=addi_op.__name__.upper(),
                ),
            ]
        else:
            raise Exception(f'Unknown phase: {phase}')
    return codes


def estimate_opposite_br_codes(isa, br_ops):
    codes = []
    table = {
        'eq': 'ne', 'ne': 'eq', 'gt': 'le', 'lt': 'ge', 'ge': 'lt', 'le': 'gt',
        'ueq': 'une', 'une': 'ueq', 'ugt': 'ule', 'ult': 'uge', 'uge': 'ult', 'ule': 'ugt',
    }
    for brkey in table.keys():
        if not br_ops[brkey] or not br_ops[table[brkey]]:
            continue
        brop0 = br_ops[brkey][0][0]
        brop1 = br_ops[table[brkey]][0][0]
        brop0 = '{{Xpu}}::{}'.format(brop0.__name__.upper())
        brop1 = '{{Xpu}}::{}'.format(brop1.__name__.upper())
        codes.append((brop0, brop1))
    return codes


def estimate_condcode_to_br_codes(isa, br_ops):
    codes = []
    for brkey in br_ops:
        if not br_ops[brkey]:
            continue
        brop = br_ops[brkey][0][0]
        condcode = 'ISD::SET{}'.format(brkey.upper())
        brop = '{{Xpu}}::{}'.format(brop.__name__.upper())
        codes.append((condcode, brop))
    return codes


def estimate_emit_frameindex_codes(isa, li_ops, load_ops, store_ops):
    load_maps = []
    for key, load_op_list in load_ops.items():
        if not load_op_list:
            continue
        load_op, dst_name, memobj, bitwidth, addrinfo = load_op_list[0]
        s = "LoadMap.insert(std::make_pair({{Xpu}}::PseudoFI_{op}, {{Xpu}}::{op}));".format(
            op=load_op.__name__.upper(),
        )
        load_maps.append(s)
    load_buildmi = [
        "BuildMI(MBB, MBBI, DL, TII->get(LoadMap[MI.getOpcode()]), MI.getOperand(0).getReg())"
    ]
    for i, param in enumerate(load_op.params.inputs.values()):
        if isa.is_reg_type(param.type_):
            s = "  .addReg(MI.getOperand({}).getReg())".format(i + 1)
        else:
            s = "  .addImm(MI.getOperand({}).getImm())".format(i + 1)
        load_buildmi.append(s)
    load_buildmi[-1] += ";"

    store_maps = []
    for key, store_op_list in store_ops.items():
        if not store_op_list:
            continue
        store_op, dst_name, memobj, bitwidth, addrinfo = store_op_list[0]
        s = "StoreMap.insert(std::make_pair({{Xpu}}::PseudoFI_{op}, {{Xpu}}::{op}));".format(
            op=store_op.__name__.upper(),
        )
        store_maps.append(s)
    store_buildmi = [
        "BuildMI(MBB, MBBI, DL, TII->get(StoreMap[MI.getOpcode()]))"
    ]
    for i, param in enumerate(store_op.params.inputs.values()):
        if isa.is_reg_type(param.type_):
            s = "  .addReg(MI.getOperand({}).getReg())".format(i)
        else:
            s = "  .addImm(MI.getOperand({}).getImm())".format(i)
        store_buildmi.append(s)
    store_buildmi[-1] += ";"

    # return (load_maps, store_maps, load_buildmi, store_buildmi)

    valname = "NewOffset"
    def get_cond(imm):
        cond = "!({val} & {mask}) && ({minv} <= ({val}>>{shift})) && (({val}>>{shift}) <= {maxv})".format(
            val=valname,
            mask=int(pow(2, imm.offset) - 1),
            shift=imm.offset,
            minv=-int(pow(2, imm.width)),
            maxv=int(pow(2, imm.width) - 1),
        )
        return cond

    # before:
    #   PseudoFI_ld/st val, fiaddr, fioff
    # aftter (small offset):
    #   ld/st val, sp, fioff+spoff
    # aftter (large offset):
    #   lui  t0, fioff_hi+spoff_hi
    #   add  dstaddr, sp, t0
    #   ld/st val, dstaddr, fioff_lo+spoff_lo
    (li32_s, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops
    load_op = load_ops["load32"][0]
    load_op, dstname, memobj, bitwidth, aaddrinfo = load_op
    load_imm = isa.get_param_obj(addrinfo[1], load_op)
    fi_addi_op, fi_addi_imm = None, None
    for ops in addi_s:
        op, imm = ops
        if imm.width >= load_imm.width and imm.offset <= load_imm.offset:
            fi_addi_op = op
            fi_addi_imm = imm
            break
    fi_lui_op, fi_lui_imm = None, None
    for ops in lui_addi_s:
        addi_op, imm = ops[1]
        if addi_op == fi_addi_op:
            fi_lui_op, fi_lui_imm = ops[0]
            break
    fi_add_op, _ = add_s[0]

    vardefs = []
    if hasattr(fi_addi_imm, "signed"):
        s = "(({val} + {half}) >> {shift}) & {mask}".format(
            val=valname,
            half=2 ** (fi_lui_imm.offset - 1),
            shift=fi_lui_imm.offset,
            mask=2 ** fi_lui_imm.width - 1,
        )
    else:
        s = "(({val} >> {shift})) & {mask}".format(
            val=valname,
            shift=fi_lui_imm.offset,
            mask=2 ** fi_lui_imm.width - 1,
        )
    if hasattr(fi_lui_imm, "signed"):
        s = "SignExtend64<{width}>({s})".format(
            width=fi_lui_imm.width,
            s=s,
        )
    vardef = "int64_t NewHi = {};".format(s)
    vardefs.append(vardef)
    s = "{val} & {mask}".format(val=valname, mask=2 ** fi_addi_imm.width - 1)
    if hasattr(fi_addi_imm, "signed"):
        s = "SignExtend64<{width}>({s})".format(width=fi_addi_imm.width, s=s)
    vardef = "int64_t NewLo = {};".format(s)
    vardefs.append(vardef)

    buildmis = []
    # lui
    buildmi = "BuildMI(MBB, MBBI, DL, TII->get({{Xpu}}::{lui_opname}), TempReg)".format(
        lui_opname=fi_lui_op.__name__.upper(),
    )
    for param in fi_lui_op.params.inputs.values():
        if isa.is_imm_type(param.type_):
            buildmi += ".addImm(NewHi)"
        else:
            buildmi += f"/*{param} {param.type_}*/ "
    buildmi += ";"
    buildmis.append(buildmi)
    # add
    buildmi = "BuildMI(MBB, MBBI, DL, TII->get({{Xpu}}::{add_opname}), TempReg)".format(
        add_opname=fi_add_op.__name__.upper(),
    )
    buildmi += ".addReg(FrameReg)"
    buildmi += ".addReg(TempReg, RegState::Kill)"
    buildmi += ";"
    buildmis.append(buildmi)
    hiadd_buildmi = buildmis

    buildmis = []
    # addi
    buildmi = "BuildMI(MBB, MBBI, DL, TII->get({{Xpu}}::{addi_opname}), MI.getOperand(0).getReg())".format(
        addi_opname=fi_addi_op.__name__.upper(),
    )
    for param in addi_op.params.inputs.values():
        if isa.is_reg_type(param.type_):
            buildmi += ".addReg(MI.getOperand(1).getReg())"
        elif isa.is_imm_type(param.type_):
            buildmi += ".addImm(MI.getOperand(2).getImm())"
        else:
            buildmi += f"/*{param} {param.type_}*/ "
    buildmi += ";"
    buildmis.append(buildmi)
    la_buildmi = buildmis

    return (load_maps, store_maps, vardefs, hiadd_buildmi, la_buildmi, load_buildmi, store_buildmi)


def estimate_long_br_codes(isa, br_ops, jump_ops, zeroreg, fixups):
    table = {
        'eq': 'ne', 'ne': 'eq', 'gt': 'le', 'lt': 'ge', 'ge': 'lt', 'le': 'gt',
        'ueq': 'une', 'une': 'ueq', 'ugt': 'ule', 'ult': 'uge', 'uge': 'ult', 'ule': 'ugt',
    }
    long_br_infos = {}
    for brkey in table.keys():
        if not br_ops[brkey] or not br_ops[table[brkey]]:
            continue
        # br ops
        br_op = br_ops[brkey][0][0]
        brinv_op = br_ops[table[brkey]][0][0]
        # opposite br ops
        name = br_op.__name__.upper()
        long_br_infos.setdefault(name, {})
        long_br_infos[name]['op'] = br_op
        long_br_infos[name]['inv'] = brinv_op.__name__.upper()
    # condition code
    beq_ops = br_ops['eq']
    brop, ltp, lnm, rtp, rnm = beq_ops[0]
    brimm_prm = list(brop.params.inputs.values())[-1]
    brimm = isa.get_param_obj(brimm_prm.label, brop)
    long_br_condition = "!isInt<{}>(Offset)".format(brimm.width + brimm.offset)
    # inst code
    codes1 = []
    codes1.append("Res.setOpcode(getRelaxedOpcode(Inst.getOpcode()));")
    for i, operand in enumerate(brop.params.inputs):
        codes1.append(f"Res.addOperand(Inst.getOperand({i}));")
    # inst code 2
    jump_op, operands = jump_ops["jump"][0]
    codes2 = []
    br_mcinst = []
    br_mcinst.append("MCInstBuilder(InvOpc)")
    for i, prm in enumerate(brop.params.inputs.values()):
        if isa.is_reg_type(prm.type_):
            codes2.append(f"MCRegister SrcReg{i + 1} = MI.getOperand({i}).getReg();")
            br_mcinst.append(f".addReg(SrcReg{i + 1})")
        else:
            codes2.append(f"MCOperand SrcSymbol = MI.getOperand({i});")
            br_mcinst.append(".addImm({})".format(brop.bin.bytesize + jump_op.bin.bytesize))
    br_mcinst.append(";")
    # codes1 = ''.join(codes2)
    # codes2 = ''.join(codes2)
    br_mcinst = ''.join(br_mcinst)
    # jump code, jump fixup
    jump_mcinst = []
    jump_mcinst.append("MCInstBuilder({{Xpu}}::{})".format(jump_op.__name__.upper()))
    for prm in list(jump_op.params.outputs.values()) + list(jump_op.params.inputs.values()):
        if isa.is_reg_type(prm.type_):
            jump_mcinst.append(f".addReg({{Xpu}}::{zeroreg})")
        else:
            jump_mcinst.append(".addOperand(SrcSymbol)")
    jump_mcinst.append(";")
    jump_mcinst = ''.join(jump_mcinst)
    jump_fixup = None
    for fixup in fixups:
        if hasattr(fixup, 'instrs') and jump_op in fixup.instrs:
            jump_fixup = "{Xpu}::fixup_{xpu}_" + fixup.name
    # br dag
    br_dags = []
    for prm in brop.params.inputs.values():
        if isa.is_reg_type(prm.type_):
            br_dags.append("{}:${}".format(prm.type_, prm.label))
        else:
            br_dags.append("Br{}:${}".format(prm.type_, prm.label))
    br_dag = ', '.join(br_dags)
    codes = {
        'infos': long_br_infos,
        'condition': long_br_condition,
        'codes1': codes1,
        'codes2': codes2,
        'br_mcinst': br_mcinst,
        'jump_mcinst': jump_mcinst,
        'jump_fixup': jump_fixup,
        'br_dag': br_dag,
    }
    return codes


class LLVMCompiler():
    target = _default_target
    triple = tuple(_default_triple)
    fixups = tuple()

    def __init__(self, isa):
        self.isa = isa
        self.outdir = "out"
        self._prepare_processorinfo()

    @property
    def namespace(self):
        return self.target

    @property
    def template_dir(self):
        return os.path.join(os.path.dirname(__file__), "template")

    def _read_template_and_write(self, fpath):
        fdirs, fname = os.path.split(fpath)
        fdirs = fdirs.split("/")
        template_fdir = os.path.join(self.template_dir, "llvm", *[d.format(Xpu="Xpu") for d in fdirs])
        template_fname = fname.format(Xpu="Xpu")
        template_fpath = os.path.join(template_fdir, template_fname)
        with open(template_fpath) as f:
            template_str = f.read()
        tmp_kwargs = dict(self.kwargs)
        tmp_kwargs.update({
            'Xpu': self.namespace,
            'XPU': self.namespace.upper(),
            'xpu': self.namespace.lower(),
        })
        final_text = Template(source=template_str).render(
            **tmp_kwargs,
        )

        out_fdir = os.path.join(self.outdir, *[d.format(Xpu=self.namespace) for d in fdirs])
        out_fname = fname.format(Xpu=self.namespace)
        out_fpath = os.path.join(out_fdir, out_fname)
        os.makedirs(out_fdir, exist_ok=True)
        with open(out_fpath, "w") as f:
            f.write(final_text)

    def _prepare_processorinfo(self):
        reginfo = self._prepare_registerinfo()
        self.kwargs = {**reginfo}
        instrinfo = self._prepare_instrinfo()
        self.kwargs = {**reginfo, **instrinfo}

    def _prepare_registerinfo(self):
        reg_base_tables = {}
        for reggroup in self.isa.registers:
            for reg in reggroup:
                reg_clsname = reg.__class__.__name__
                reg_base_tables.setdefault(reg_clsname, list())
                reg_base_tables[reg_clsname].append(reg)
        reg_bases = []
        for name, regs in reg_base_tables.items():
            # if name == "Register":
            #     continue
            max_no = max([r.number for r in regs])
            reg_bases.append(RegisterBase(
                name=name,
                bitsize=max_no.bit_length(),
            ))

        reg_defs = []
        reg_labels = []
        for reggroup in self.isa.registers:
            # if reggroup.label == "PCR":
            #     continue
            for reg in reggroup:
                if reg.label in reg_labels:
                    continue
                reg_labels.append(reg.label)
                reg_defs.append(RegisterDef(
                    namespace=self.namespace,
                    varname=reg.label.upper(),
                    basename=reg.__class__.__name__,
                    no=reg.number,
                    name=reg.label,
                    has_aliases=(len(reg.aliases) > 0),
                    aliases="[{}]".format(",".join('"{}"'.format(n) for n in reg.aliases)),
                    dwarfno=reg.dwarf_number,
                ))

        def reg_varname(reg, reggroup):
            if reggroup.label == "GPR":
                return reg.label.upper()
            else:
                return "{}_{}".format(reg.label, reggroup.label).upper()

        regcls_defs = []
        for reggroup in self.isa.registers:
            # if reggroup.label == "PCR":
            #     continue
            reg_varnames = ["{}::{}".format(
                self.namespace, reg.label.upper()) for reg in reggroup]
            reg_varnames = ',\n'.join(reg_varnames)
            regcls_defs.append(RegisterClassDef(
                varname=reggroup.label,
                regs=reggroup.regs,
                # reg_varnames=reg_varnames,
                reg_varnames=','.join([reg.label.upper() for reg in reggroup]),
                bitsize=int(len(reggroup.regs) - 1).bit_length(),
            ))

        reserved_regs = []
        gpr = next(filter(lambda rg: rg.label == "GPR", self.isa.registers), None)
        reg0 = None
        sp = None
        fp = None
        ra = None
        arg_regs = []
        ret_regs = []
        callee_saved_regs = []
        if gpr:
            for reg in gpr.regs:
                if any([
                    reg.is_zero, reg.is_return_address, reg.is_stack_pointer, reg.is_global_pointer,
                ]):
                    reserved_regs.append(reg.label.upper())
                if reg0 is None and (reg.is_zero):
                    reg0 = reg.label.upper()
                if sp is None and (reg.is_stack_pointer):
                    sp = reg.label.upper()
                if fp is None and (reg.is_frame_pointer):
                    fp = reg.label.upper()
                if ra is None and (reg.is_return_address):
                    ra = reg.label.upper()
            regs = list(filter(lambda r: r.is_arg, gpr.regs))
            # arg_regs = ', '.join(["{}::{}".format(self.namespace, r.label.upper()) for r in regs])
            # arg_regs = ', '.join([r.label.upper() for r in regs])
            arg_regs = [r.label.upper() for r in regs]
            regs = list(filter(lambda r: r.is_ret, gpr.regs))
            ret_regs = [r.label.upper() for r in regs]
            ret_reg_numbers = [r.number for r in regs]
            regs = list(filter(lambda r: r.is_callee_saved, gpr.regs))
            callee_saved_regs = [r.label.upper() for r in regs]

        kwargs = {
            "reg_bases": reg_bases,
            "reg_defs": reg_defs,
            "regcls_defs": regcls_defs,
            "reserved_regs": reserved_regs,
            "gpr": gpr,
            "REG0": reg0,
            "SP": sp,
            "FP": fp,
            "RA": ra,

            "ra_and_callee_saved_regs": [ra] + callee_saved_regs,
            "callee_saved_regs": callee_saved_regs,
            "arg_regs": arg_regs,
            "ret_regs": ret_regs,
            "ret_reg_numbers": ret_reg_numbers,
        }
        return kwargs

    def _prepare_instrinfo(self):
        reg0 = self.kwargs['REG0']

        # -- InstrInfo.td --
        asm_operand_clss = []
        operand_clss = []
        operand_types = []
        for imm in self.isa.immediates:
            operand_cls = OperandCls(
                varname=imm.label,
                basecls="i32",
            )
            if isinstance(imm.enums, dict):
                asm_operand_cls = AsmOperandCls(
                    name=imm.label,
                    enums=imm.enums,
                )
                asm_operand_clss.append(asm_operand_cls)
                operand_cls.asm_operand_cls = asm_operand_cls
                operand_cls.imm_leaf = None
            else:
                operand_cls.asm_operand_cls = None
                cond = "return !(Imm & {mask}) && ({minv} <= (Imm>>{shift})) && ((Imm>>{shift}) <= {maxv});".format(
                    mask=int(pow(2, imm.offset) - 1),
                    shift=imm.offset,
                    minv=-int(pow(2, imm.width)),
                    maxv=int(pow(2, imm.width) - 1),
                )
                operand_cls.imm_leaf = OperandType(
                    varname=imm.label + "Tp",
                    basecls="i32",
                    cond=cond,
                )
            operand_clss.append(operand_cls)
        for mem in self.isa.memories:
            operand_clss.append(OperandCls(
                varname=mem.label,
                basecls="i32",
            ))

        br_imm_operand_clss = []
        for instr in self.isa.instructions:
            instr_def = InstrDefs()
            if m := may_change_pc_relative(instr):
                imm_key = m
                if imm_key.startswith("ins."):
                    imm_key = imm_key[4:]
                else:
                    continue
                param_obj = self.isa.get_param_obj(imm_key, instr)
                if not isinstance(param_obj, Immediate):
                    continue
                cls = param_obj
                brcls = "Br" + cls.label
                # brcls = "Br" + cls
                operand_cls = OperandCls(
                    varname=brcls,
                    basecls="OtherVT",
                )
                operand_cls.br_attr = BrImmOperandAttr(
                    width=cls.width,
                    offset=cls.offset,
                )
                if brcls not in (o.varname for o in br_imm_operand_clss):
                    br_imm_operand_clss.append(operand_cls)

        instr_defs = []
        for instr in self.isa.instructions:
            pc_relative = may_change_pc_relative(instr)

            instr_def = InstrDefs()
            instr_def.varname = instr.__name__.upper()
            # instr_def.ins = ', '.join([
            #     '{}:${}'.format(cls, label) for label, cls in instr.prm.inputs.items()
            # ])
            instr_def.ins = []
            for label, cls in instr.prm.inputs.items():
                brcls = "Br" + cls
                if pc_relative and brcls in (o.varname for o in br_imm_operand_clss):
                    cls = brcls
                instr_def.ins.append('{}:${}'.format(cls, label))
            instr_def.ins = ", ".join(instr_def.ins)

            # instr_def.outs = ', '.join([
            #     '{}:${}'.format(cls, label) for label, cls in instr.prm.outputs.items()
            # ])
            instr_def.outs = []
            duplicated_outs = {}
            for label, cls in instr.prm.outputs.items():
                if label in instr.prm.inputs.keys():
                    new_label = label + "_o"
                    duplicated_outs[label] = new_label
                    label = new_label
                instr_def.outs.append('{}:${}'.format(cls, label))
            instr_def.outs = ", ".join(instr_def.outs)

            asmstrs = []
            for ast in instr.asm.ast:
                if ast == '$opn':
                    asmstrs += [instr.opn]
                elif ast[0] == "$":
                    asmstrs += ["${{{}}}".format(ast[1:])]
                else:
                    asmstrs += [ast]
            instr_def.asmstr = '"{}"'.format(''.join(asmstrs))

            instr_def.pattern = get_instr_pattern(instr)

            params = []
            # params.append("  let DecoderNamespace = \"{}\";".format(
            #     f"{self.namespace}{instr.bitsize}",
            # ))
            params.append("  let Size = {};".format(
                instr.bin.bytesize,
            ))
            if duplicated_outs:
                params.append("  let Constraints = \"{}\";".format(','.join(
                    ["${} = ${}".format(
                        il, ol,
                    ) for il, ol in duplicated_outs.items()]
                )))
            params = "\n".join(params)
            instr_def.params = params

            bitss_by_name = dict()
            for bits in instr.bin.bitss:
                bitss_by_name.setdefault(bits.label, list())
                bitss_by_name[bits.label].append(bits)

            bit_defs = []
            for label, bitss in reversed(bitss_by_name.items()):
                if label == "$opc":
                    pass
                else:
                    bitss_size = sum([b.size() for b in bitss])
                    bit_defs.append("  bits<{}> {};".format(
                        bitss_size,
                        label[1:],
                    ))
            bit_instrs = []
            bits_sum = 0
            for bits in reversed(instr.bin.bitss):
                if bits.label == "$opc":
                    bits_value = (instr.opc >> bits_sum) & (2 ** (bits.size()) - 1)
                    let_str = ""
                    if bits.size() == 1:
                        let_str += "  let Inst{{{}}} = ".format(bits_sum)
                    else:
                        let_str += "  let Inst{{{}-{}}} = ".format(
                            bits_sum + bits.size() - 1,
                            bits_sum,
                        )
                    let_str += "{};".format(bits_value)
                    bit_instrs.append(let_str)
                else:
                    param_obj = self.isa.get_param_obj(bits.label[1:], instr)
                    param_offset = 0
                    if isinstance(param_obj, Immediate):
                        param_offset = param_obj.offset
                    # print(instr.opn, bits.label[1:], param_offset)
                    let_str = ""
                    if bits.size() == 1:
                        let_str += "  let Inst{{{}}} = ".format(bits_sum)
                    else:
                        let_str += "  let Inst{{{}-{}}} = ".format(
                            bits_sum + bits.size() - 1,
                            bits_sum,
                        )
                    if bits.size() == 1:
                        let_str += "{}{{{}}};".format(bits.label[1:], bits.lsb - param_offset)
                    else:
                        let_str += "{}{{{}-{}}};".format(
                            bits.label[1:],
                            bits.msb - param_offset,
                            bits.lsb - param_offset,
                        )
                    bit_instrs.append(let_str)
                bits_sum += bits.size()
            instr_def.bit_defs = "\n".join(bit_defs)
            instr_def.bit_insts = "\n".join(bit_instrs)

            attrs = []
            instr_attrs = [f for f in dir(instr)]
            for k, vv in instr_attr_table.items():
                # if not hasattr(instr, k):
                if k not in instr_attrs:
                    continue
                try:
                    cond = getattr(instr, k) is True
                except Exception:
                    # if instr_attr is a method, set attr forcely as trial.
                    cond = True
                if cond:
                    if isinstance(vv, str):
                        vv = [vv]
                    for v in vv:
                        if v not in attrs:
                            attrs.append(v)
            attrs.sort()
            attrs = [f"  let {x} = true;"for x in attrs]
            instr_def.attrs = "\n".join(attrs)

            instr_defs.append(instr_def)

        # gen pc manipulation ops
        jump_ops = estimate_jump_ops(self.isa)
        call_ops = estimate_call_ops(self.isa)
        ret_ops = estimate_ret_ops(self.isa)

        load_ops = estimate_load_ops(self.isa)
        store_ops = estimate_store_ops(self.isa)

        # prepare load immediate
        li_ops = estimate_load_immediate_ops(self.isa)

        # gen load immediate
        xforms, dags = estimate_load_immediate_dag(self.isa, li_ops)
        li_pat_fmt = "def : Pat<({immtp}:$imm), ({opstr})>;"
        li_pats = [li_pat_fmt.format(immtp=immtp, opstr=opstr) for immtp, opstr in dags]
        gen_li_defs = "\n".join(xforms) + "\n\n" + "\n".join(li_pats)
        li32_dag = dags[0][1]

        instr_bitsizes = list(set([ins().bitsize for ins in self.isa.instructions]))

        # gen branchs
        cmp_ops = estimate_compare_branch_ops(self.isa)
        br_ops = estimate_branch_ops(self.isa)
        setcc_ops = estimate_setcc_ops(self.isa)
        dags = estimate_branch_dag(self.isa, cmp_ops, br_ops, setcc_ops, reg0)
        br_dags = dags

        # gen load/store
        defs, pats = estimate_load_dag(self.isa, load_ops)
        def_load_dags = []
        for line in defs:
            def_load_dags.append(line.format(Xpu=self.namespace))
        pat_load_dags = []
        for line in pats:
            pat_load_dags.append(line.format(Xpu=self.namespace))

        defs, pats = estimate_store_dag(self.isa, store_ops)
        def_store_dags = []
        for line in defs:
            def_store_dags.append(line.format(Xpu=self.namespace))
        pat_store_dags = []
        for line in pats:
            pat_store_dags.append(line.format(Xpu=self.namespace))

        # gen pseudocall
        pseudo_jump_dag = estimate_pseudo_jump_dag(self.isa, jump_ops)
        pseudo_jumpind_dag = estimate_pseudo_jumpind_dag(self.isa, jump_ops)
        pseudo_ret_dag = estimate_pseudo_ret_dag(self.isa, ret_ops)
        pseudo_call_dag = estimate_pseudo_call_dag(self.isa, call_ops)
        pseudo_callind_dag = estimate_pseudo_callind_dag(self.isa, call_ops)
        pseudo_call_asm = estimate_pseudo_call_asm(self.isa, call_ops)

        # llvm/lib/Target/Xpu/AsmParser/
        asm_operand_clss = []
        for imm in self.isa.immediates:
            if isinstance(imm.enums, dict):
                asm_operand_cls = AsmOperandCls(
                    name=imm.label,
                    enums=imm.enums,
                )
                asm_operand_clss.append(asm_operand_cls)

        # llvm/lib/Target/Xpu/MCTargetDesc/XpuAsmBackend.cpp
        if len(self.fixups) > 0:
            fixups = self.fixups[:]
        else:
            fixups = auto_make_fixups(self.isa, li_ops, call_ops)
        for fixup in fixups:
            fixup.namespace = self.namespace
            fixup.name_enum = f"fixup_{fixup.namespace.lower()}_{fixup.name}"
        self._fixups = fixups

        fixups = self._fixups
        fixups_should_force_reloc = list()
        fixups_adjust = fixups[:]
        relax_instrs = list()
        fixups_pc_rel = [fx for fx in fixups if fx.name[:6] == "pc_rel"]
        fixups_pc_use = [fx for fx in fixups if fx.name[:6] == "pc_use"]
        fixup_relocs = [fx for fx in fixups if not isinstance(fx.bin, int)]
        fixup_call = next(filter(lambda fx: fx.name == "call", fixups), None)

        instr_aliases = []
        for alias in self.isa.instruction_aliases:
            instr_alias = get_instr_alias(alias, self.isa)
            if instr_alias:
                srcstr, dstnode = instr_alias
                dstnode = "({} {})".format(dstnode[0], ", ".join(dstnode[1:]))
                instr_alias = 'InstAlias<"{}", {}>'.format(srcstr, dstnode)
                instr_aliases.append(instr_alias)

        # llvm/lib/Target/Xpu/MCTargetDesc/XpuMCCodeEmitter.cpp
        _codes = estimate_mc_expand_longcall_codes(self.isa, call_ops)
        mc_longcall_codes = []
        for line in _codes:
            line = line.format(Xpu=self.namespace)
            mc_longcall_codes.append(line)

        _codes = estimate_mc_expand_call_codes(self.isa, call_ops)
        mc_call_codes = []
        for line in _codes:
            line = line.format(Xpu=self.namespace)
            mc_call_codes.append(line)

        # llvm/lib/Target/Xpu/XpuInstrInfo.cpp
        _codes = estimate_add_immediate_codes(self.isa, li_ops)
        addimm_codes = []
        for cond, vardefs, buildmis in _codes:
            vardefs = (var.format(Xpu=self.namespace) for var in vardefs)
            buildmis = (bmi.format(Xpu=self.namespace) for bmi in buildmis)
            addimm_codes.append((cond, vardefs, buildmis))

        (li32, li_s, lui_s, addi_s, lui_addi_s, add_s) = li_ops
        copy_reg_buildmi = estimate_copy_reg_buildmi(self.isa, [], addi_s, add_s, reg0)
        copy_reg_buildmi = copy_reg_buildmi.format(Xpu=self.namespace)

        _codes = estimate_opposite_br_codes(self.isa, br_ops)
        opposite_br_codes = []
        for brop0, brop1 in _codes:
            brop0 = brop0.format(Xpu=self.namespace)
            brop1 = brop1.format(Xpu=self.namespace)
            opposite_br_codes.append((brop0, brop1))

        # llvm/lib/Target/Xpu/XpuISelDAGToDAG.cpp
        _codes = estimate_selectaddr_codes(self.isa, li_ops, has_addr=True)
        selectaddr_addr_imm_codes = []
        for cond, vardefs, sdvalues in _codes:
            vardefs = (var.format(Xpu=self.namespace) for var in vardefs)
            sdvalues = (bmi.format(Xpu=self.namespace) for bmi in sdvalues)
            selectaddr_addr_imm_codes.append((cond, vardefs, sdvalues))

        _codes = estimate_selectaddr_codes(self.isa, li_ops, has_addr=False)
        selectaddr_imm_codes = []
        for cond, vardefs, sdvalues in _codes:
            vardefs = (var.format(Xpu=self.namespace) for var in vardefs)
            sdvalues = (bmi.format(Xpu=self.namespace, REG0=reg0) for bmi in sdvalues)
            selectaddr_imm_codes.append((cond, vardefs, sdvalues))

        # llvm/lib/Target/Xpu/XpuISelLowering.cpp
        _codes = estimate_getaddr_codes(self.isa, li_ops, phase='la')  # lla, lga, la
        getaddr_la_sdvalue_codes = []
        for code in _codes:
            code = code.format(Xpu=self.namespace)
            getaddr_la_sdvalue_codes.append(code)

        cc_to_br_codes = []
        _codes = estimate_condcode_to_br_codes(self.isa, br_ops)
        for cc, br in _codes:
            br = br.format(Xpu=self.namespace)
            code = (cc, br)
            cc_to_br_codes.append(code)

        # llvm/lib/Target/Xpu/XpuRegisterInfo.cpp
        _codes = estimate_emit_frameindex_codes(self.isa, li_ops, load_ops, store_ops)
        load_maps, store_maps, vardef, hiadd_buildmi, la_buildmi, load_buildmi, store_buildmi = _codes
        frameindex_load_maps = []
        for line in load_maps:
            frameindex_load_maps.append(line.format(Xpu=self.namespace))
        frameindex_store_maps = []
        for line in store_maps:
            frameindex_store_maps.append(line.format(Xpu=self.namespace))
        frameindex_vardef = [x.format(Xpu=self.namespace) for x in vardef]
        frameindex_hiadd_buildmi = [x.format(Xpu=self.namespace) for x in hiadd_buildmi]
        frameindex_la_buildmi = [x.format(Xpu=self.namespace) for x in la_buildmi]
        frameindex_load_buildmi = [x.format(Xpu=self.namespace) for x in load_buildmi]
        frameindex_store_buildmi = [x.format(Xpu=self.namespace) for x in store_buildmi]

        # long branch codes
        codes = estimate_long_br_codes(self.isa, br_ops, jump_ops, reg0, fixups)
        codes['jump_mcinst'] = codes['jump_mcinst'].format(Xpu=self.namespace)
        codes['jump_fixup'] = codes['jump_fixup'].format(
            Xpu=self.namespace, xpu=self.namespace.lower()
        )
        long_br_codes = codes

        kwargs = {
            "asm_operand_clss": asm_operand_clss,
            "operand_clss": operand_clss,
            "operand_types": operand_types,
            "br_imm_operand_clss": br_imm_operand_clss,
            "instr_defs": instr_defs,
            "gen_li_defs": gen_li_defs,
            "li32_dag": li32_dag,
            "br_dags": br_dags,
            "def_load_dags": def_load_dags,
            "def_store_dags": def_store_dags,
            "pat_load_dags": pat_load_dags,
            "pat_store_dags": pat_store_dags,
            "pseudo_jump_dag": pseudo_jump_dag,
            "pseudo_jumpind_dag": pseudo_jumpind_dag,
            "pseudo_ret_dag": pseudo_ret_dag,
            "pseudo_call_dag": pseudo_call_dag,
            "pseudo_callind_dag": pseudo_callind_dag,
            "pseudo_call_asm": pseudo_call_asm,

            "instr_bitsizes": instr_bitsizes,

            "asm_operand_clss": asm_operand_clss,

            "fixups": fixups,
            "fixups_should_force_reloc": fixups_should_force_reloc,
            "fixups_adjust": fixups_adjust,
            "relax_instrs": relax_instrs,

            "fixups_pc_rel": fixups_pc_rel,
            "fixups_pc_use": fixups_pc_use,
            "fixup_relocs": fixup_relocs,
            "fixup_call": fixup_call,

            "instr_aliases": instr_aliases,

            "mc_longcall_codes": mc_longcall_codes,
            "mc_call_codes": mc_call_codes,

            "addimm_codes": addimm_codes,
            "copy_reg_buildmi": copy_reg_buildmi,
            "opposite_br_codes": opposite_br_codes,

            "selectaddr_addr_imm_codes": selectaddr_addr_imm_codes,
            "selectaddr_imm_codes": selectaddr_imm_codes,

            "getaddr_la_sdvalue_codes": getaddr_la_sdvalue_codes,
            "cc_to_br_codes": cc_to_br_codes,

            "frameindex_load_maps": frameindex_load_maps,
            "frameindex_store_maps": frameindex_store_maps,
            "frameindex_vardef": frameindex_vardef,
            "frameindex_hiadd_buildmi": frameindex_hiadd_buildmi,
            "frameindex_la_buildmi": frameindex_la_buildmi,
            "frameindex_load_buildmi": frameindex_load_buildmi,
            "frameindex_store_buildmi": frameindex_store_buildmi,

            "long_br_codes": long_br_codes,
        }
        return kwargs

    def gen_llvm_srcs(self):
        self.gen_llvm_clang_srcs()
        self.gen_llvm_lld_srcs()
        self.gen_llvm_llvm_srcs()

    def gen_llvm_clang_srcs(self):
        fpaths = (
            "clang/include/clang/Basic/Builtins{Xpu}.def",
            "clang/include/clang/Basic/TargetBuiltins.h",
            "clang/lib/Basic/Targets/{Xpu}.cpp",
            "clang/lib/Basic/Targets/{Xpu}.h",
            "clang/lib/Basic/Targets.cpp",
            "clang/lib/Basic/CMakeLists.txt",
            "clang/lib/Driver/ToolChains/BareMetal.cpp",
        )
        for fpath in fpaths:
            self._read_template_and_write(fpath)

    def gen_llvm_lld_srcs(self):
        fpaths = (
            "lld/ELF/Arch/{Xpu}.cpp",
            "lld/ELF/CMakeLists.txt",
            "lld/ELF/Target.cpp",
            "lld/ELF/Target.h",
        )
        for fpath in fpaths:
            self._read_template_and_write(fpath)

    def gen_llvm_llvm_srcs(self):
        fpaths = (
            "llvm/CMakeLists.txt",
            "llvm/include/llvm/BinaryFormat/ELFRelocs/{Xpu}.def",
            "llvm/include/llvm/BinaryFormat/ELF.h",
            "llvm/include/llvm/Object/ELFObjectFile.h",
            "llvm/include/llvm/TargetParser/Triple.h",
            "llvm/include/module.modulemap",
            "llvm/lib/Object/ELF.cpp",
            "llvm/lib/Target/{Xpu}/CMakeLists.txt",
            "llvm/lib/Target/{Xpu}/{Xpu}.h",
            "llvm/lib/Target/{Xpu}/{Xpu}.td",
            "llvm/lib/Target/{Xpu}/{Xpu}AsmPrinter.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}CallingConv.td",
            "llvm/lib/Target/{Xpu}/{Xpu}RegisterInfo.td",
            "llvm/lib/Target/{Xpu}/{Xpu}RegisterInfo.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}RegisterInfo.h",
            "llvm/lib/Target/{Xpu}/{Xpu}InstrInfo.td",
            "llvm/lib/Target/{Xpu}/{Xpu}InstrInfo.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}InstrInfo.h",
            "llvm/lib/Target/{Xpu}/{Xpu}FrameLowering.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}FrameLowering.h",
            "llvm/lib/Target/{Xpu}/{Xpu}ISelLowering.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}ISelLowering.h",
            "llvm/lib/Target/{Xpu}/{Xpu}ISelDAGToDAG.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}ISelDAGToDAG.h",
            "llvm/lib/Target/{Xpu}/{Xpu}MachineFunctionInfo.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}MachineFunctionInfo.h",
            "llvm/lib/Target/{Xpu}/{Xpu}Schedule.td",
            "llvm/lib/Target/{Xpu}/{Xpu}Subtarget.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}Subtarget.h",
            "llvm/lib/Target/{Xpu}/{Xpu}TargetMachine.cpp",
            "llvm/lib/Target/{Xpu}/{Xpu}TargetMachine.h",
            "llvm/lib/Target/{Xpu}/AsmParser/CMakeLists.txt",
            "llvm/lib/Target/{Xpu}/AsmParser/{Xpu}AsmParser.cpp",
            "llvm/lib/Target/{Xpu}/Disassembler/CMakeLists.txt",
            "llvm/lib/Target/{Xpu}/Disassembler/{Xpu}Disassembler.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/CMakeLists.txt",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}AsmBackend.h",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}AsmBackend.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}BaseInfo.h",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}ELFObjectWriter.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}FixupKinds.h",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}InstPrinter.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}InstPrinter.h",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCAsmInfo.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCAsmInfo.h",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCCodeEmitter.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCExpr.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCExpr.h",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCTargetDesc.cpp",
            "llvm/lib/Target/{Xpu}/MCTargetDesc/{Xpu}MCTargetDesc.h",
            "llvm/lib/Target/{Xpu}/TargetInfo/CMakeLists.txt",
            "llvm/lib/Target/{Xpu}/TargetInfo/{Xpu}TargetInfo.cpp",
            "llvm/lib/Target/{Xpu}/TargetInfo/{Xpu}TargetInfo.h",
            "llvm/lib/TargetParser/Triple.cpp",
        )
        for fpath in fpaths:
            self._read_template_and_write(fpath)

    def gen_compiler_rt_srcs(self):
        pwd = os.getcwd()
        os.chdir(os.path.join(self.template_dir, "llvm"))
        files = glob.glob("compiler-rt/**/*", recursive=True)
        files = [f for f in files if os.path.isfile(f)]
        os.chdir(pwd)

        for fpath in files:
            fdirs, fname = os.path.split(fpath)
            fdirs = fdirs.split("/")
            template_fdir = os.path.join(self.template_dir, "llvm", *fdirs)
            template_fname = fname
            template_fpath = os.path.join(template_fdir, template_fname)
            with open(template_fpath) as f:
                template_str = f.read()
            # final_text = template_str
            tmp_kwargs = dict(self.kwargs)
            tmp_kwargs.update({
                'Xpu': self.namespace,
                'XPU': self.namespace.upper(),
                'xpu': self.namespace.lower(),
                'target_triple': self.triple,
            })
            final_text = Template(source=template_str).render(
                **tmp_kwargs,
            )

            out_fdir = os.path.join(self.outdir, *[d.replace("xpu", self.target.lower()) for d in fdirs])
            out_fname = fname.replace("xpu", self.target.lower())
            out_fpath = os.path.join(out_fdir, out_fname)
            os.makedirs(out_fdir, exist_ok=True)
            with open(out_fpath, "w") as f:
                f.write(final_text)

    def gen_picolibc_srcs(self):
        pwd = os.getcwd()
        os.chdir(os.path.join(self.template_dir, "picolibc"))
        files = glob.glob("**/*", recursive=True)
        files = [f for f in files if os.path.isfile(f)]
        os.chdir(pwd)

        for fpath in files:
            fdirs, fname = os.path.split(fpath)
            fdirs = fdirs.split("/")
            template_fdir = os.path.join(self.template_dir, "picolibc", *fdirs)
            template_fname = fname
            template_fpath = os.path.join(template_fdir, template_fname)
            with open(template_fpath) as f:
                template_str = f.read()
            # final_text = template_str
            tmp_kwargs = dict(self.kwargs)
            tmp_kwargs.update({
                'Xpu': self.namespace,
                'XPU': self.namespace.upper(),
                'xpu': self.namespace.lower(),
                'target_triple': self.triple,
            })
            final_text = Template(source=template_str).render(
                **tmp_kwargs,
            )

            out_fdir = os.path.join(self.outdir, *[d.replace("xpu", self.target.lower()) for d in fdirs])
            out_fname = fname.replace("xpu", self.target.lower())
            out_fpath = os.path.join(out_fdir, out_fname)
            os.makedirs(out_fdir, exist_ok=True)
            with open(out_fpath, "w") as f:
                f.write(final_text)
