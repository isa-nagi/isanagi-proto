from isana.compiler import LLVMCompiler
from isana.compiler import Relocation

from .defs import xlen
from .instructionI import (
    beq, bne, blt, bge, bltu, bgeu,
    jal, auipc, jalr, lui,
    addi, slti, sltiu, xori, ori, andi, lb, lh, lw, lbu, lhu, lwu, ld,
    sb, sh, sw, sd,
    add
)
from .instructionC import c_beqz, c_bnez, c_jal, c_j, c_lui


instrs_b = [beq, bne, blt, bge, bltu, bgeu]
instrs_j = [jal]
instrs_call = [auipc, jalr]
instrs_pcrel_hi = [auipc]
instrs_hi = [lui]
instrs_lo_i = [addi, slti, sltiu, xori, ori, andi, lb, lh, lw, lbu, lhu]
instrs_lo_s = [sb, sh, sw]
if xlen == 64:
    instrs_lo_i += [lwu, ld]
    instrs_lo_s += [sd]
instrs_add = [add]
instrs_cb = [c_beqz, c_bnez]
instrs_cj = [c_jal, c_j]
instrs_clui = [c_lui]

relocations = [
    Relocation(number=0  , name="NONE"             , size=32),  # noqa
    Relocation(number=1  , name="32"               , size=32),  # noqa
    Relocation(number=2  , name="64"               , size=64),  # noqa
    Relocation(number=3  , name="RELATIVE"         , size=32),  # noqa
    Relocation(number=4  , name="COPY"             , size=32),  # noqa
    Relocation(number=5  , name="JUMP_SLOT"        , size=32),  # noqa
    # Relocation(number=6  , name="TLS_DTPMOD32"     , size=32),  # noqa
    # Relocation(number=7  , name="TLS_DTPMOD64"     , size=32),  # noqa
    # Relocation(number=8  , name="TLS_DTPREL32"     , size=32),  # noqa
    # Relocation(number=9  , name="TLS_DTPREL64"     , size=32),  # noqa
    # Relocation(number=10 , name="TLS_TPREL32"      , size=32),  # noqa
    # Relocation(number=11 , name="TLS_TPREL64"      , size=32),  # noqa
    # Relocation(number=12 , name="TLSDESC"          , size=32),  # noqa
    Relocation(number=16 , name="BRANCH"           , size=32, is_pcrel=True, instrs=instrs_b[:]),  # noqa
    Relocation(number=17 , name="JAL"              , size=32, is_pcrel=True, instrs=instrs_j[:]),  # noqa
    Relocation(number=18 , name="CALL"             , size=64, is_pcrel=True, is_call=True, instrs=instrs_call[:]),  # noqa
    # Relocation(number=19 , name="CALL_PLT"         , size=64, is_plt_pcrel=True, is_call=True, instrs=instrs_call[:]),  # noqa
    # Relocation(number=20 , name="GOT_HI20"         , size=32, is_got_pcrel=True, expr="%got_pcrel_hi($expr)"),  # noqa
    # Relocation(number=21 , name="TLS_GOT_HI20"     , size=32, is_got_pcrel=True),  # noqa
    # Relocation(number=22 , name="TLS_GD_HI20"      , size=32, is_tlsgd_pcrel=True),  # noqa
    Relocation(number=23 , name="PCREL_HI20"       , size=32, is_pcrel=True, expr="%pcrel_hi($expr)",  instrs=instrs_pcrel_hi[:]),  # noqa
    Relocation(number=24 , name="PCREL_LO12_I"     , size=32, is_pcrel=True, expr="%pcrel_lo($expr)",  instrs=instrs_lo_i[:]),  # noqa
    Relocation(number=25 , name="PCREL_LO12_S"     , size=32, is_pcrel=True, expr="%pcrel_lo($expr)",  instrs=instrs_lo_s[:]),  # noqa
    Relocation(number=26 , name="HI20"             , size=32,                expr="%hi($expr)",        instrs=instrs_hi[:]),  # noqa
    Relocation(number=27 , name="LO12_I"           , size=32,                expr="%lo($expr)",        instrs=instrs_lo_i[:]),  # noqa
    Relocation(number=28 , name="LO12_S"           , size=32,                expr="%lo($expr)",        instrs=instrs_lo_s[:]),  # noqa
    # Relocation(number=29 , name="TPREL_HI20"       , size=32,                expr="%tprel_hi($expr)",  instrs=instrs_pcrel_hi[:]),  # noqa
    # Relocation(number=30 , name="TPREL_LO12_I"     , size=32,                expr="%tprel_lo($expr)",  instrs=instrs_lo_i[:]),  # noqa
    # Relocation(number=31 , name="TPREL_LO12_S"     , size=32,                expr="%tprel_lo($expr)",  instrs=instrs_lo_s[:]),  # noqa
    # Relocation(number=32 , name="TPREL_ADD"        , size=32,                expr="%tprel_add($expr)", instrs=instrs_add[:]),  # noqa
    Relocation(number=33 , name="ADD8"             , size=8 ),  # noqa
    Relocation(number=34 , name="ADD16"            , size=16),  # noqa
    Relocation(number=35 , name="ADD32"            , size=32),  # noqa
    Relocation(number=36 , name="ADD64"            , size=64),  # noqa
    Relocation(number=37 , name="SUB8"             , size=8 ),  # noqa
    Relocation(number=38 , name="SUB16"            , size=16),  # noqa
    Relocation(number=39 , name="SUB32"            , size=32),  # noqa
    Relocation(number=40 , name="SUB64"            , size=64),  # noqa
    # Relocation(number=41 , name="GOT32_PCREL"      , size=32, is_got_pcrel=True),  # noqa
    Relocation(number=43 , name="ALIGN"            , size=32),  # noqa
    Relocation(number=44 , name="RVC_BRANCH"       , size=16, is_pcrel=True, instrs=instrs_cb[:]),  # noqa
    Relocation(number=45 , name="RVC_JUMP"         , size=16, is_pcrel=True, instrs=instrs_cj[:]),  # noqa
    Relocation(number=46 , name="RVC_LUI"          , size=16, instrs=instrs_clui[:]),  # noqa
    Relocation(number=51 , name="RELAX"            , size=32),  # noqa
    Relocation(number=52 , name="SUB6"             , size=8 ),  # noqa
    Relocation(number=53 , name="SET6"             , size=8 ),  # noqa
    Relocation(number=54 , name="SET8"             , size=8 ),  # noqa
    Relocation(number=55 , name="SET16"            , size=16),  # noqa
    Relocation(number=56 , name="SET32"            , size=32),  # noqa
    Relocation(number=57 , name="32_PCREL"         , size=32, is_pcrel=True),  # noqa
    Relocation(number=58 , name="IRELATIVE"        , size=32),  # noqa
    # Relocation(number=59 , name="PLT32"            , size=32, is_plt_pcrel=True),  # noqa
    Relocation(number=60 , name="SET_ULEB128"      , size=128),  # noqa
    Relocation(number=61 , name="SUB_ULEB128"      , size=128),  # noqa
    # Relocation(number=62 , name="TLSDESC_HI20"     , size=32, is_tlsdesc_pcrel=True, expr="%tlsdesc_hi($expr)"     ),  # noqa
    # Relocation(number=63 , name="TLSDESC_LOAD_LO12", size=32, is_tlsdesc_pcrel=True, expr="%tlsdesc_load_lo($expr)"),  # noqa
    # Relocation(number=64 , name="TLSDESC_ADD_LO12" , size=32, is_tlsdesc_pcrel=True, expr="%tlsdesc_load_lo($expr)"),  # noqa
    # Relocation(number=65 , name="TLSDESC_CALL"     , size=32, is_tlsdesc_pcrel=True, expr="%tlsdesc_call($expr)"   ),  # noqa
    Relocation(number=191, name="VENDOR"           , size=32),  # noqa
]


class RiscvXCompiler(LLVMCompiler):
    target = "RiscvXpu"
    triple = "riscvxpu32le-unknown-elf"

    relocations = relocations

    def __init__(self, isa, **kwargs):
        super().__init__(isa, **kwargs)


compiler = RiscvXCompiler
