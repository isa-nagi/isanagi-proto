from isana.model.riscvx.python.isa import isa
from isana import semantic
from pprint import pprint  # noqa


class TestSemantic():
    def semantic_1(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] + ctx.GPR[ins.rs2]

    def semantic_2(self, ctx, ins):
        ctx.GPR[ins.rd] = ctx.GPR[ins.rs1] + ins.imm


if __name__ == "__main__":
    # instr = next(filter(lambda x: x.opn == "add", isa.instructions), None)
    # ret = semantic.get_alu_dag(instr.semantic)
    # print(ret)

    # ret = semantic.get_alu_dag(TestSemantic().semantic_1)
    # print(ret)

    instructions = isa.instructions
    li_ops = semantic.estimate_load_immediate_dag(isa)
    pprint(li_ops)
