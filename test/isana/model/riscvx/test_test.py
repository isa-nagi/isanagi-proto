from isana.model.riscvx.python.isa import isa
from isana.test import InstructionTest


def test_test_generation():
    instr = next(filter(lambda x: x.opn == "addi", isa.instructions), None)
    tester = InstructionTest(isa, instr)
    tester.reg_alias = False

    # cases = tester.gen_binary_edge_case()
    # cases = tester.gen_binary_random_case(repeat=10)
    cases = tester.gen_asm_edge_case()
    # cases = tester.gen_asm_random_case(repeat=10)

    cases = tester.merge_case(cases)
    for testcase in cases:
        print(testcase)


if __name__ == '__main__':
    test_test_generation()
