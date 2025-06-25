import os
import re
import glob
from jinja2 import Template
from isana.semantic import (
    may_change_pc_absolute,
    may_change_pc_relative,
    may_take_memory_address,
    get_alu_dag,
    estimate_load_immediate_dag,
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
    )

    def __init__(self, **kwargs):
        self.target = kwargs.pop('target', _default_target)
        self.number = kwargs.pop('number', -1)
        self.name = kwargs.pop('name', str())
        self.addend = kwargs.pop('addend', None)
        self.bin = kwargs.pop('bin', None)
        self.name_enum = f"fixup_{self.target.lower()}_{self.name}"
        self.reloc_procs = list()
        super().__init__(**kwargs)


def auto_make_fixups(isa):
    fixups = list()
    fixups += auto_make_relocations(isa)
    return fixups


def auto_make_relocations(isa):
    relocs = {
        "pc_abs": list(),
        "pc_rel": list(),
        "mem_addr": list(),
        "other_imm": list(),
    }
    instrs = dict()
    for cls in isa.instructions:
        if not hasattr(cls, 'semantic'):
            continue
        instr = cls()
        instr.isa = isa
        bin_filtered = re.sub(r"\$(?!opc|imm)\w+", r"$_", str(instr.bin))
        relocinfo = (instr.bitsize, bin_filtered)
        instr.decode(instr.opc)  # dummy decode as all parameter is 0
        if may_change_pc_absolute(instr):
            key = "pc_abs"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(cls)
        elif may_change_pc_relative(instr):
            key = "pc_rel"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(cls)
        elif may_take_memory_address(instr.semantic):
            key = "mem_addr"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(cls)
        elif "imm" in instr.prm.inputs.keys():  # TODO fix condition
            key = "other_imm"
            relocs[key].append(relocinfo)
            instrs.setdefault((key, bin_filtered), list())
            instrs[(key, bin_filtered)].append(cls)
        else:
            pass
    fixups = list()
    fixups += [
        Fixup(name="32", offset=0, size=32, flags=0, bin=32),
        Fixup(name="64", offset=0, size=64, flags=0, bin=64),
    ]
    for key in relocs:
        relocs[key] = sorted(list(set(relocs[key])), key=lambda x: str(x[1]))
        for ri, info in enumerate(relocs[key]):
            bitsize, bin_ = info
            fixup = Fixup()
            fixup.name = f"{key}_{ri}"
            fixup.offset = 0
            fixup.size = bitsize  # TODO: fix it
            if key == "pc_rel":
                fixup.flags = "MCFixupKindInfo::FKF_IsPCRel"
            else:
                fixup.flags = "0"  # TODO: fix it
            fixup.bin = bin_
            fixup.instrs = [i() for i in sorted(list(set(instrs[(key, bin_)])), key=lambda x: x.opn)]
            fixups.append(fixup)
    instr_reloc_table = dict()

    for fixup in fixups:
        procs = list()
        if fixup.bin is None:
            pass
        if isinstance(fixup.bin, int):
            procs.append("  | val")
        else:
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
        if fixup in instr_reloc_table.keys():
            fixup.instrs = instr_reloc_table[fixup]
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
        dstnode = "({} {})".format(dstnode[0], ", ".join(dstnode[1:]))
        s = 'InstAlias<"{}", {}>'.format(srcstr, dstnode)
        return s


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
            reg0 = gpr.regs[0].label.upper()
            for reg in gpr.regs:
                if any([
                    reg.is_zero, reg.is_return_address, reg.is_stack_pointer, reg.is_global_pointer,
                ]):
                    reserved_regs.append(reg.label.upper())
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
        for cls in self.isa.instructions:
            instr = cls()
            instr.isa = self.isa
            instr.decode(instr.opc)  # dummy decode as all parameter is 0
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
        for cls in self.isa.instructions:
            instr = cls()
            instr.isa = self.isa
            instr.decode(instr.opc)  # dummy decode as all parameter is 0
            instr_def = InstrDefs()

            pc_relative = may_change_pc_relative(instr)

            instr_def.varname = instr.__class__.__name__.upper()
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
                instr.bytesize,
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

        # gen load immediate
        xforms, dags = estimate_load_immediate_dag(self.isa)
        li_pat_fmt = "def : Pat<({immtp}:$imm), ({opstr})>;"
        li_pats = [li_pat_fmt.format(immtp=immtp, opstr=opstr) for immtp, opstr in dags]
        gen_li_defs = "\n".join(xforms) + "\n\n" + "\n".join(li_pats)
        li32_dag = dags[0][1]

        instr_bitsizes = list(set([ins().bitsize for ins in self.isa.instructions]))

        # llvm/lib/Target/Xpu/AsmParser/
        asm_operand_clss = []
        for imm in self.isa.immediates:
            if isinstance(imm.enums, dict):
                asm_operand_cls = AsmOperandCls(
                    name=imm.label,
                    enums=imm.enums,
                )
                asm_operand_clss.append(asm_operand_cls)

        # llvm/lib/Target/Xpu/MCTargetDesc/AsmBackend.cpp
        if len(self.fixups) > 0:
            fixups = self.fixups[:]
        else:
            fixups = auto_make_fixups(self.isa)
        for fixup in fixups:
            fixup.namespace = self.namespace
            fixup.name_enum = f"fixup_{fixup.namespace.lower()}_{fixup.name}"
        self._fixups = fixups

        fixups = self._fixups
        fixups_should_force_reloc = list()
        fixups_adjust = fixups[:]
        relax_instrs = list()
        fixups_pc_rel = [fx for fx in fixups if fx.name[:6] == "pc_rel"]
        fixup_relocs = [fx for fx in fixups if not isinstance(fx.bin, int)]

        instr_aliases = []
        for alias in self.isa.instruction_aliases:
            instr_alias = get_instr_alias(alias, self.isa)
            if instr_alias:
                instr_aliases.append(instr_alias)

        kwargs = {
            "asm_operand_clss": asm_operand_clss,
            "operand_clss": operand_clss,
            "operand_types": operand_types,
            "br_imm_operand_clss": br_imm_operand_clss,
            "instr_defs": instr_defs,
            "gen_li_defs": gen_li_defs,
            "li32_dag": li32_dag,

            "instr_bitsizes": instr_bitsizes,

            "asm_operand_clss": asm_operand_clss,

            "fixups": fixups,
            "fixups_should_force_reloc": fixups_should_force_reloc,
            "fixups_adjust": fixups_adjust,
            "relax_instrs": relax_instrs,

            "fixups_pc_rel": fixups_pc_rel,
            "fixup_relocs": fixup_relocs,

            "instr_aliases": instr_aliases,
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
