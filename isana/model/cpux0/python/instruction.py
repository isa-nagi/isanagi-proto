from isana.isa import Instruction, parameter, assembly, binary
from isana.isa import unsigned
# from isana.isa import signed


class InstrA(Instruction):
    prm = parameter("ra:GPR", "rb:GRP, rc:GPR, cx:ImmS12")
    asm = assembly("$opn $ra, $rb, $rc, $cx")
    bin = binary("$opc[31:24], $ra[3:0], $rb[3:0], $rc[3:0], $cx[11:0]")


class InstrArrr(Instruction):
    prm = parameter("ra:GPR", "rb:GRP, rc:GPR")
    asm = assembly("$opn $ra, $rb, $rc")
    bin = binary("$opc[31:24], $ra[3:0], $rb[3:0], $rc[3:0], $opc[11:0]")


class InstrArr(Instruction):
    prm = parameter("ra:GPR", "rb:GRP")
    asm = assembly("$opn $ra, $rb")
    bin = binary("$opc[31:24], $ra[3:0], $rb[3:0], $opc[15:12], $opc[11:0]")


class InstrArri(Instruction):
    prm = parameter("ra:GPR", "rb:GRP, cx:ImmS16")
    asm = assembly("$opn $ra, $rb, $cx")
    bin = binary("$opc[31:24], $ra[3:0], $rb[3:0], $cx[15:0]")


class InstrAssrr(Instruction):
    prm = parameter("hi:SPR, lo:SPR", "ra:GPR, rb:GRP")
    asm = assembly("$opn $ra, $rb")
    bin = binary("$opc[31:24], $ra[3:0], $rb[3:0], $opc[15:12], $opc[11:0]")


class InstrL(Instruction):
    prm = parameter("ra:GPR", "rb:GRP, cx:ImmS16")
    asm = assembly("$opn $ra, $rb, $cx")
    bin = binary("$opc[31:24], $ra[3:0], $rb[3:0], $cx[15:0]")


class InstrJ(Instruction):
    prm = parameter("", "cx:ImmS24")
    asm = assembly("$opn, $cx")
    bin = binary("$opc[31:24], $cx[23:0]")


class nop(InstrJ):
    opn, opc = "NOP", 0b00000000_000000000000000000000000

    def semantic(self, ctx, ins):
        pass


class ld(InstrL):
    opn, opc = "LD", 0b00000001_0000_0000_0000000000000000
    is_load = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.GPR[ins.ra] = ctx.Mem.read(32, addr)


class st(InstrL):
    opn, opc = "ST", 0b00000010_0000_0000_0000000000000000
    is_store = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.Mem.write(32, addr, ctx.GPR[ins.ra])


class lb(InstrL):
    opn, opc = "LB", 0b00000011_0000_0000_0000000000000000
    is_load = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.GPR[ins.ra] = ctx.Mem.read(32, addr)


class lbu(InstrL):
    opn, opc = "LBu", 0b00000100_0000_0000_0000000000000000
    is_load = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.GPR[ins.ra] = unsigned(8, ctx.Mem.read(8, addr))


class sb(InstrL):
    opn, opc = "SB", 0b00000101_0000_0000_0000000000000000
    is_store = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.Mem.write(8, addr, ctx.GPR[ins.ra])


class lh(InstrL):
    opn, opc = "LH", 0b00000110_0000_0000_0000000000000000
    is_load = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.GPR[ins.ra] = ctx.Mem.read(16, addr)


class lhu(InstrL):
    opn, opc = "LHu", 0b00000111_0000_0000_0000000000000000
    is_load = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.GPR[ins.ra] = unsigned(16, ctx.Mem.read(16, addr))


class sh(InstrL):
    opn, opc = "SH", 0b00001000_0000_0000_0000000000000000
    is_store = True

    def semantic(self, ctx, ins):
        addr = ctx.GPR[ins.rb] + ins.cx
        ctx.Mem.write(16, addr, ctx.GPR[ins.ra])


class addiu(InstrL):
    opn, opc = "ADDiu", 0b00001001_0000_0000_0000000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] + ins.cx


class andi(InstrL):
    opn, opc = "ANDi", 0b00001100_0000_0000_0000000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] & ins.cx


class ori(InstrL):
    opn, opc = "ORi", 0b00001101_0000_0000_0000000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] | ins.cx


class xori(InstrL):
    opn, opc = "XORi", 0b00001110_0000_0000_0000000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] ^ ins.cx


class lui(InstrL):
    opn, opc = "LUi", 0b00001111_0000_0000_0000000000000000
    prm = parameter("ra:GPR", "cx:ImmS16O16")
    asm = assembly("$opn $ra, $cx")
    bin = binary("$opc[31:24], $ra[3:0], $opc[19:16], $cx[15:0]")

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ins.cx


class addu(InstrArrr):
    opn, opc = "ADDu", 0b00010001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = unsigned(32, ctx.GPR[ins.rb]) + unsigned(32, ctx.GPR[ins.rc])


class subu(InstrArrr):
    opn, opc = "ADDu", 0b00010010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = unsigned(32, ctx.GPR[ins.rb]) - unsigned(32, ctx.GPR[ins.rc])


class add(InstrArrr):
    opn, opc = "ADD", 0b00010011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] + ctx.GPR[ins.rc]


class sub(InstrArrr):
    opn, opc = "SUB", 0b00010100_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] - ctx.GPR[ins.rc]


class clz(InstrArr):
    opn, opc = "clz", 0b00010101_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        # ctx.GPR[ins.ra] = ctx.builtin.clz(ctx.GPR[ins.rb])
        pass


class clo(InstrArr):
    opn, opc = "CLO", 0b00010110_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        # ctx.GPR[ins.ra] = ctx.builtin.clo(ctx.GPR[ins.rb])
        pass


class mul(InstrArrr):
    opn, opc = "MUL", 0b00010111_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] * ctx.GPR[ins.rc]


class and_(InstrArrr):
    opn, opc = "AND", 0b00011000_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] & ctx.GPR[ins.rc]


class or_(InstrArrr):
    opn, opc = "OR", 0b00011001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] | ctx.GPR[ins.rc]


class xor(InstrArrr):
    opn, opc = "XOR", 0b00011010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] ^ ctx.GPR[ins.rc]


class nor(InstrArrr):
    opn, opc = "NOR", 0b00011011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ~(ctx.GPR[ins.rb] | ctx.GPR[ins.rc])


class rol(InstrArri):
    opn, opc = "ROL", 0b00011100_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        # ctx.GPR[ins.ra] = ctx.buildin.rol(ctx.GPR[ins.rb], ins.cx)
        pass


class ror(InstrArri):
    opn, opc = "ROR", 0b00011101_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        # ctx.GPR[ins.ra] = ctx.buildin.ror(ctx.GPR[ins.rb], ins.cx)
        pass


class shl(InstrArri):
    opn, opc = "SHL", 0b00011110_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] << ins.cx


class shr(InstrArri):
    opn, opc = "SHR", 0b00011111_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = unsigned(32, ctx.GPR[ins.rb]) >> ins.cx


class sra(InstrArri):
    opn, opc = "SRA", 0b00100000_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] >> ins.cx


class srav(InstrArrr):
    opn, opc = "SRAV", 0b00100001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] >> ctx.GPR[ins.rc]


class shlv(InstrArrr):
    opn, opc = "SHLV", 0b00100010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] << ctx.GPR[ins.rc]


class shrv(InstrArrr):
    opn, opc = "SHRV", 0b00100011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = unsigned(32, ctx.GPR[ins.rb]) >> ctx.GPR[ins.rc]


class rolv(InstrArrr):
    opn, opc = "ROL", 0b00100100_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        # ctx.GPR[ins.ra] = ctx.buildin.rol(ctx.GPR[ins.rb], ctx.GPR[ins.rc])
        pass


class rorv(InstrArrr):
    opn, opc = "ROR", 0b00100101_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        # ctx.GPR[ins.ra] = ctx.buildin.ror(ctx.GPR[ins.rb], ctx.GPR[ins.rc])
        pass


class cmp(InstrArri):
    opn, opc = "CMP", 0b00101010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.SR[0] = ctx.builtin.cmp(ins.cx, ins.ra, ins.rb)


class cmpu(InstrArri):
    opn, opc = "CMPu", 0b00101011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.SR[0] = ctx.builtin.cmp(ins.cx, unsigned(32, ins.ra), unsigned(32, ins.rb))


class jeq(InstrJ):
    opn, opc = "JEQ", 0b00110000_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.SR[0].N == 0 and ctx.SR[0].Z == 1
        if cond:
            ctx.C0R.pc += ins.cx


class jne(InstrJ):
    opn, opc = "JNE", 0b00110001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.SR[0].N == 1 and ctx.SR[0].Z == 1
        if cond:
            ctx.C0R.pc += ins.cx


class jlt(InstrJ):
    opn, opc = "JLT", 0b00110010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.SR[0].N == 0 and ctx.SR[0].Z == 0
        if cond:
            ctx.C0R.pc += ins.cx


class jgt(InstrJ):
    opn, opc = "JGT", 0b00110011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.SR[0].N == 1 and ctx.SR[0].Z == 0
        if cond:
            ctx.C0R.pc += ins.cx


class jle(InstrJ):
    opn, opc = "JLE", 0b00110100_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.SR[0].N == 0 and ctx.SR[0].Z == 0  # TODO: fix it
        if cond:
            ctx.C0R.pc += ins.cx


class jge(InstrJ):
    opn, opc = "JGE", 0b00110101_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.SR[0].N == 1 and ctx.SR[0].Z == 0  # TODO: fix it
        if cond:
            ctx.C0R.pc += ins.cx


class jmp(InstrJ):
    opn, opc = "JMP", 0b00110110_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.C0R.pc += ins.cx


class jalr(InstrJ):
    opn, opc = "JALR", 0b00111001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[14] = ctx.C0R.pc
        ctx.C0R.pc = ctx.GPR[ins.rb]


class bal(InstrJ):
    opn, opc = "BAL", 0b00111010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[14] = ctx.C0R.pc
        ctx.C0R.pc += ins.cx


class jsub(InstrJ):
    opn, opc = "JSUB", 0b00111011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[14] = ctx.C0R.pc
        ctx.C0R.pc += ins.cx


class jr(InstrJ):
    opn, opc = "JR", 0b00111100_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.C0R.pc = ctx.GPR[14]


class mult(InstrAssrr):
    opn, opc = "MULT", 0b01000001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.SPR.hi = (ctx.GPR[ins.ra] * ctx.GPR[ins.rb]) << 32
        ctx.SPR.lo = ctx.GPR[ins.ra] * ctx.GPR[ins.rb]


class multu(InstrAssrr):
    opn, opc = "MULTU", 0b01000010_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.SPR.hi = (unsigned(32, ctx.GPR[ins.ra]) * unsigned(32, ctx.GPR[ins.rb])) << 32
        ctx.SPR.lo = unsigned(32, ctx.GPR[ins.ra]) * unsigned(32, ctx.GPR[ins.rb])


class div(InstrAssrr):
    opn, opc = "DIV", 0b01000011_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.SPR.hi = ctx.GPR[ins.ra] % ctx.GPR[ins.rb]
        ctx.SPR.lo = ctx.GPR[ins.ra] // ctx.GPR[ins.rb]


class divu(InstrAssrr):
    opn, opc = "DIVU", 0b01000100_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.SPR.hi = unsigned(32, ctx.GPR[ins.ra]) % unsigned(32, ctx.GPR[ins.rb])
        ctx.SPR.lo = unsigned(32, ctx.GPR[ins.ra]) // unsigned(32, ctx.GPR[ins.rb])


class mfhi(InstrA):
    opn, opc = "MFHI", 0b01000110_0000_0000_0000_000000000000
    prm = parameter("ra:GPR", "hi:SPR")
    asm = assembly("$opn $ra")
    bin = binary("$opc[31:24], $ra[3:0], $opc[19:16], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.SPR.hi


class mflo(InstrA):
    opn, opc = "MFLO", 0b01000111_0000_0000_0000_000000000000
    prm = parameter("ra:GPR", "lo:SPR")
    asm = assembly("$opn $ra")
    bin = binary("$opc[31:24], $ra[3:0], $opc[19:16], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.SPR.lo


class mthi(InstrA):
    opn, opc = "MTHI", 0b01001000_0000_0000_0000_000000000000
    prm = parameter("ra:GPR", "hi:SPR")
    asm = assembly("$opn $ra")
    bin = binary("$opc[31:24], $ra[3:0], $opc[19:16], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.SPR.hi = ctx.GPR[ins.ra]


class mtlo(InstrA):
    opn, opc = "MTLO", 0b01001001_0000_0000_0000_000000000000
    prm = parameter("ra:GPR", "lo:SPR")
    asm = assembly("$opn $ra")
    bin = binary("$opc[31:24], $ra[3:0], $opc[19:16], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.SPR.lo = ctx.GPR[ins.ra]


class mfc0(InstrA):
    opn, opc = "MFC0", 0b01010000_0000_0000_0000_000000000000
    prm = parameter("ra:GPR", "rb:C0R")
    asm = assembly("$opn $ra, $rb")
    bin = binary("$opc[31:24], $ra[3:0], $opc[19:17], $rb[0], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.C0R[ins.rb]


class mtc0(InstrA):
    opn, opc = "MTC0", 0b01010001_0000_0000_0000_000000000000
    prm = parameter("ra:C0R", "rb:GPR")
    asm = assembly("$opn $ra, $rb")
    bin = binary("$opc[31:24], $opc[23:21], $ra[0], $rb[3:0], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.C0R[ins.ra] = ctx.GPR[ins.rb]


class c0mov(InstrA):
    opn, opc = "C0MOV", 0b01010010_0000_0000_0000_000000000000
    prm = parameter("ra:C0R", "rb:C0R")
    asm = assembly("$opn $ra, $rb")
    bin = binary("$opc[31:24], $opc[23:21], $ra[0], $opc[19:17], $rb[0], $opc[15:12], $opc[11:0]")

    def semantic(self, ctx, ins):
        ctx.C0R[ins.ra] = ctx.C0R[ins.rb]


class slti(InstrJ):
    opn, opc = "SLTi", 0b00010110_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] < ins.cx


class sltiu(InstrJ):
    opn, opc = "SLTiu", 0b00010111_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = unsigned(32, ctx.GPR[ins.rb]) < ins.cx


class slt(InstrJ):
    opn, opc = "SLT", 0b00011000_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = ctx.GPR[ins.rb] < ctx.GPR[ins.rc]


class sltu(InstrJ):
    opn, opc = "SLT", 0b00011001_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        ctx.GPR[ins.ra] = unsigned(32, ctx.GPR[ins.rb]) < unsigned(32, ctx.GPR[ins.rc])


class beq(InstrJ):
    opn, opc = "BEQ", 0b00110111_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.GPR[ins.ra] == ctx.GPR[ins.rb]
        if cond:
            ctx.C0R.pc += ins.cx


class bne(InstrJ):
    opn, opc = "BNE", 0b00111000_0000_0000_0000_000000000000

    def semantic(self, ctx, ins):
        cond = ctx.GPR[ins.ra] != ctx.GPR[ins.rb]
        if cond:
            ctx.C0R.pc += ins.cx


instructions = [
    nop,
    ld,
    st,
    lb,
    lbu,
    sb,
    lh,
    lhu,
    sh,
    addiu,
    andi,
    ori,
    xori,
    lui,
    addu,
    subu,
    add,
    sub,
    clz,
    clo,
    mul,
    and_,
    or_,
    xor,
    nor,
    rol,
    ror,
    shl,
    shr,
    sra,
    srav,
    shlv,
    shrv,
    rolv,
    rorv,
    cmp,
    cmpu,
    jeq,
    jne,
    jlt,
    jgt,
    jle,
    jge,
    jmp,
    jalr,
    bal,
    jsub,
    jr,
    mult,
    multu,
    div,
    divu,
    mfhi,
    mflo,
    mthi,
    mtlo,
    mfc0,
    mtc0,
    c0mov,
]

instructions += [
    slti,
    sltiu,
    slt,
    sltu,
    beq,
    bne,
]
