from isana.isa import InstructionAlias, PseudoInstruction


# for medlow code model
#   lui  rd, %hi(symbol)
#   addi rd, %lo(symbol)
# for medany code model
#   label: auipc rd, %pcrel_hi(symbol)
#          addi  rd, %pcrel_lo(label)(rd)
instruction_aliases = [
    PseudoInstruction("la $rd, $symbol", ["lui $rd, %hi($symbol)",  # for non-PIC
                                          "addi $rd, $rd, %lo($symbol)"],
                      is_load_address=True),
    # PseudoInstruction("la $rd, $symbol", ["lui $rd, %hi($symbol)",  # for PIC
    #                                       "lw $rd, %lo($symbol) ($rd)"],
    #                   is_load_address=True),
    PseudoInstruction("lla $rd, $symbol", ["lui $rd, %hi($symbol)",
                                           "addi $rd, $rd, %lo($symbol)"],
                      is_load_address=True),
    PseudoInstruction("lb $rd, $symbol", ["lui $rd, %hi($symbol)",
                                          "lb $rd, %lo($symbol) ($rd)"]),
    PseudoInstruction("lh $rd, $symbol", ["lui $rd, %hi($symbol)",
                                          "lh $rd, %lo($symbol) ($rd)"]),
    PseudoInstruction("lw $rd, $symbol", ["lui $rd, %hi($symbol)",
                                          "lw $rd, %lo($symbol) ($rd)"]),
    # PseudoInstruction("ld $rd, $symbol", ["lui $rd, %hi($symbol)",
    #                                       "ld $rd, %lo($symbol) ($rd)"]),
    PseudoInstruction("sb $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
                                               "sb $rd, %lo($symbol) ($rt)"]),
    PseudoInstruction("sh $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
                                               "sh $rd, %lo($symbol) ($rt)"]),
    PseudoInstruction("sw $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
                                               "sw $rd, %lo($symbol) ($rt)"]),
    # PseudoInstruction("sd $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
    #                                            "sd $rd, %lo($symbol) ($rt)"]),
    PseudoInstruction("flw $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
                                                "flw $rd, %lo($symbol) ($rt)"]),
    # PseudoInstruction("fld $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
    #                                             "fld $rd, %lo($symbol) ($rt)"]),
    PseudoInstruction("fsw $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
                                                "fsw $rd, %lo($symbol) ($rt)"]),
    # PseudoInstruction("fsd $rd, $symbol, $rt", ["lui $rd, %hi($symbol)",
    #                                             "fsd $rd, %lo($symbol) ($rt)"]),

    InstructionAlias("nop", ["addi x0, x0, 0"]),
    PseudoInstruction("li $rd, $imm", ["lui $rd, $imm",
                                       "addi $rd, $rd, $imm"],
                      is_load_immediate=True),
    InstructionAlias("mv $rd, $rs", ["addi $rd, $rs, 0"]),
    InstructionAlias("not $rd, $rs", ["xori $rd, $rs, -1"]),
    InstructionAlias("neg $rd, $rs", ["sub $rd, x0, $rs"]),
    InstructionAlias("negw $rd, $rs", ["subw $rd, x0, $rs"]),
    InstructionAlias("sext.w $rd, $rs", ["addiw $rd, $rs, 1"]),
    InstructionAlias("seqz $rd, $rs", ["sltiu $rd, $rs, 1"]),
    InstructionAlias("snez $rd, $rs", ["sltu $rd, x0, $rs"]),
    InstructionAlias("sltz $rd, $rs", ["slt $rd, $rs, x0"]),
    InstructionAlias("sgtz $rd, $rs", ["slt $rd, x0, $rs"]),

    InstructionAlias("fmv.s $rd, $rs", ["fsgnj.s $rd, $rs, $rs"]),
    InstructionAlias("fabs.s $rd, $rs", ["fsgnjx.s $rd, $rs, $rs"]),
    InstructionAlias("fneg.s $rd, $rs", ["fsgnjn.s $rd, $rs, $rs"]),
    InstructionAlias("fmv.d $rd, $rs", ["fsgnj.d $rd, $rs, $rs"]),
    InstructionAlias("fabs.d $rd, $rs", ["fsgnjx.d $rd, $rs, $rs"]),
    InstructionAlias("fneg.d $rd, $rs", ["fsgnjn.d $rd, $rs, $rs"]),

    InstructionAlias("beqz $rs, $offset", ["beq $rs, x0, $offset"]),
    InstructionAlias("bnez $rs, $offset", ["bne $rs, x0, $offset"]),
    InstructionAlias("blez $rs, $offset", ["bge x0, $rs, $offset"]),
    InstructionAlias("bgez $rs, $offset", ["bge $rs, x0, $offset"]),
    InstructionAlias("bltz $rs, $offset", ["blt $rs, x0, $offset"]),
    InstructionAlias("bgtz $rs, $offset", ["blt x0, $rs, $offset"]),

    InstructionAlias("bgt $rs, $rt, $offset", ["blt $rt, $rs, $offset"]),
    InstructionAlias("ble $rs, $rt, $offset", ["bge $rt, $rs, $offset"]),
    InstructionAlias("bgtu $rs, $rt, $offset", ["bltu $rt, $rs, $offset"]),
    InstructionAlias("bleu $rs, $rt, $offset", ["bgeu $rt, $rs, $offset"]),

    InstructionAlias("j $offset", ["jal x0, $offset"]),
    InstructionAlias("jal $offset", ["jal x1, $offset"]),
    InstructionAlias("jr $rs", ["jalr x0, $rs, 0"]),
    InstructionAlias("jalr $rs", ["jalr x1, $rs, 0"]),
    InstructionAlias("ret", ["jalr x0, x1, 0"]),
    PseudoInstruction("call $symbol", ["auipc x1, %pcrel_hi($symbol)",
                                       "jalr x1, x1, %pcrel_lo($symbol)"],
                      is_call=True),
    PseudoInstruction("tail $symbol", ["auipc x6, %pcrel_hi($symbol)",
                                       "jalr x0, x6, %pcrel_lo($symbol)"],
                      is_tail=True),

    InstructionAlias("fence", ["fence 15, 15"]),  # ["fence iorw, iorw"]

    InstructionAlias("rdinstret $rd", ["csrrs $rd, instret, x0"]),
    InstructionAlias("rdinstreth $rd", ["csrrs $rd, instreth, x0"]),
    InstructionAlias("rdcycle $rd", ["csrrs $rd, cycle, x0"]),
    InstructionAlias("rdcycleh $rd", ["csrrs $rd, cycleh, x0"]),
    InstructionAlias("rdtime $rd", ["csrrs $rd, time, x0"]),
    InstructionAlias("rdtimeh $rd", ["csrrs $rd, timeh, x0"]),

    InstructionAlias("csrr $rd, $csr", ["csrrs $rd, $csr, x0"]),
    InstructionAlias("csrw $csr, $rs", ["csrrw x0, $csr, $rs"]),
    InstructionAlias("csrs $csr, $rs", ["csrrs x0, $csr, $rs"]),
    InstructionAlias("csrc $csr, $rs", ["csrrc x0, $csr, $rs"]),

    InstructionAlias("csrwi $csr, $imm", ["csrrwi x0, $csr, $imm"]),
    InstructionAlias("csrsi $csr, $imm", ["csrrsi x0, $csr, $imm"]),
    InstructionAlias("csrci $csr, $imm", ["csrrci x0, $csr, $imm"]),

    InstructionAlias("frcsr $rd", ["csrrs $rd, fcsr, x0"]),
    InstructionAlias("fscsr $rd, $rs", ["csrrs $rd, fcsr, $rs"]),
    InstructionAlias("fscsr $rs", ["csrrs x0, fcsr, $rs"]),

    InstructionAlias("frrm $rd", ["csrrs $rd, frm, x0"]),
    InstructionAlias("fsrm $rd, $rs", ["csrrs $rd, frm, $rs"]),
    InstructionAlias("fsrm $rs", ["csrrs x0, frm, $rs"]),

    InstructionAlias("frflags $rd", ["csrrs $rd, fflags, x0"]),
    InstructionAlias("fsflags $rd, $rs", ["csrrs $rd, fflags, $rs"]),
    InstructionAlias("fsflags $rs", ["csrrs x0, fflags, $rs"]),
]
