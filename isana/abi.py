from isana.semantic import (
    estimate_call_ops,
    estimate_ret_ops,
    estimate_jump_ops,
    estimate_compare_branch_ops,
    estimate_branch_ops,
    estimate_setcc_ops,
    estimate_load_ops,
    estimate_store_ops,
    estimate_load_immediate_ops,
)


class ABI():
    def __init__(self, isa, **kwargs):
        self.isa = isa
        self.endian = kwargs.pop('endian', 'little')
        self.bits = kwargs.pop('bits', 32)
        self.c_type_sizes = {
            'bool': 1,
            'char': 1,
            'short': 2,
            'int': 4,
            'long': self.bits // 8,
            'long long': 8,
            'float': 4,
            'double': 8,
            'ptr': self.bits // 8,
        }
        self.c_type_aligns = {k: v for k, v in self.c_type_sizes.items()}
        self.sp_align = 16

        self.gpr = None
        self.pc_reg = None
        self.zero_reg = None
        self.ra_reg = None
        self.sp_reg = None
        self.fp_reg = None
        self.gp_reg = None
        self.tp_reg = None
        self.arg_regs = None
        self.ret_regs = None
        self.callee_saved_regs = None
        self.caller_saved_regs = None

        self.call_ops = None
        self.ret_ops = None
        self.jump_ops = None
        self.cmp_ops = None
        self.br_ops = None
        self.setcc_ops = None
        self.load_ops = None
        self.store_ops = None
        self.li_ops = None
        self.la_ops = None

        self.relocations = kwargs.pop('relocations', list())

    def autofill_info(self):
        self.gpr = next(filter(lambda g: g.is_gpr, self.isa.registers), None)
        all_regs = [reg for grp in self.isa.registers for reg in grp]
        gpr_regs = self.gpr.regs[:]
        self.pc_reg = next(filter(lambda r: r.is_pc, all_regs), None)
        self.zero_reg = next(filter(lambda r: r.is_zero, gpr_regs), None)
        self.ra_reg = next(filter(lambda r: r.is_return_address, gpr_regs), None)
        self.sp_reg = next(filter(lambda r: r.is_stack_pointer, gpr_regs), None)
        self.fp_reg = next(filter(lambda r: r.is_frame_pointer, gpr_regs), None)
        self.gp_reg = next(filter(lambda r: r.is_global_pointer, gpr_regs), None)
        self.tp_reg = next(filter(lambda r: r.is_thread_local_pointer, gpr_regs), None)
        self.arg_regs = [r for r in gpr_regs if r.is_arg]
        self.ret_regs = [r for r in gpr_regs if r.is_ret]
        self.callee_saved_regs = [r for r in gpr_regs if r.is_callee_saved]
        self.caller_saved_regs = [r for r in gpr_regs if r.is_caller_saved]

        self.call_ops = estimate_call_ops(self.isa)
        self.ret_ops = estimate_ret_ops(self.isa)
        self.jump_ops = estimate_jump_ops(self.isa)
        self.cmp_ops = estimate_compare_branch_ops(self.isa)
        self.br_ops = estimate_branch_ops(self.isa)
        self.setcc_ops = estimate_setcc_ops(self.isa)
        self.load_ops = estimate_load_ops(self.isa)
        self.store_ops = estimate_store_ops(self.isa)
        self.li_ops = estimate_load_immediate_ops(self.isa)
        # self.la_ops = estimate_load_address_ops(self.isa)


class Relocation():
    def __init__(self, **kwargs):
        # self.target = kwargs.pop('target', _default_target)
        self.number = kwargs.pop('number', -1)
        self.name = kwargs.pop('name', str())
        self.addend = kwargs.pop('addend', None)
        self.bin = kwargs.pop('bin', None)
        self.offset = kwargs.pop('offset', 0)
        self.size = kwargs.pop('size', 0)
        self.flags = kwargs.pop('flags', 0)
        # self.name_enum = f"fixup_{self.target.lower()}_{self.name}"
        self.is_call = kwargs.pop('is_call', False)
        self.is_pcrel = kwargs.pop('is_pcrel', False)
        self.reloc_procs = list()
        self.val_carryed = str()
        for k, v in kwargs.items():
            setattr(self, k, v)
