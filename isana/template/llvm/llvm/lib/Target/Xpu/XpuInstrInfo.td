//=== AsmOperandClasses
{% for asmopcls in asm_operand_clss -%}
def {{ asmopcls.name }}AsmOp: AsmOperandClass {
  let Name = "{{ asmopcls.name }}AsmOp";
  let PredicateMethod = "isImm";
  let RenderMethod = "addImmOperands";
  let ParserMethod = "parse{{ asmopcls.name }}AsmOp";
}
{% endfor %}

//=== Operands
{% for opcls in operand_clss -%}
{% if opcls.asm_operand_cls -%}
def {{ opcls.varname }}: Operand<{{ opcls.basecls }}> {
  let ParserMatchClass = {{ opcls.asm_operand_cls.name }}AsmOp;
  let PrintMethod = "print{{ opcls.asm_operand_cls.name }}";
}
{% elif opcls.imm_leaf -%}
def {{ opcls.varname }}: Operand<{{ opcls.basecls }}>, ImmLeaf<{{ opcls.basecls }}, [{ {{ opcls.imm_leaf.cond }} }]>;
{% else -%}
def {{ opcls.varname }}: Operand<{{ opcls.basecls }}>;
{% endif -%}
{% endfor %}

class BrImmS<int n, int s> : Operand<OtherVT> {
  let OperandType   = "OPERAND_PCREL";
  let EncoderMethod = "getImmOpValueRShift<" # s # ">";
  let DecoderMethod = "decodeSImmOperand<" # n # "," # s # ">";
}
{% for opcls in br_imm_operand_clss -%}
def {{ opcls.varname }}: BrImmS<{{ opcls.br_attr.width }},{{ opcls.br_attr.offset }}>;
{% endfor %}

//=== Instruction Classes
class {{ Xpu }}Inst<dag outs, dag ins, string asmstr, list<dag> pattern>: Instruction {
  let Namespace = "{{ Xpu }}";
  field bits<32> Inst;
  let Size = 4;
  let OutOperandList = outs;
  let InOperandList  = ins;
  let AsmString   = asmstr;
  let Pattern     = pattern;
  let DecoderNamespace = "{{ Xpu }}";
  field bits<32> SoftFail = 0;
}

//=== Instruction Defs
{% for inst in instr_defs -%}
def {{ inst.varname }}: {{ Xpu }}Inst<
  (outs {{ inst.outs }}), (ins {{ inst.ins }}),
  {{ inst.asmstr }},
  {{ inst.pattern }}>
{
{{ inst.params }}
{{ inst.bit_defs }}
{{ inst.bit_insts }}
{{ inst.attrs }}
}
{% endfor %}

//=== Pseudo Instruction Defs
def {{ xpu }}_ret_glue : SDNode<
  "{{ Xpu }}ISD::RET_GLUE", SDTNone,
  [SDNPHasChain, SDNPOptInGlue, SDNPVariadic]>;

def PseudoRET: {{ Xpu }}Inst<
  (outs), (ins),
  "",
  [({{ xpu }}_ret_glue)]>,
  PseudoInstExpansion<({{ pseudo_ret_dag }})>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let isBarrier = 1;
  let isReturn = 1;
  let isTerminator = 1;
}


//== Generate Immediate Pattern
{{ gen_li_defs }}

//== Set-ConditionCode Pattern

def : Pat<(seteq GPR:$rs1, GPR:$rs2), (SLTIU (XOR GPR:$rs1, GPR:$rs2), 1)>;
def : Pat<(setne GPR:$rs1, GPR:$rs2), (SLTU X0, (XOR GPR:$rs1, GPR:$rs2))>;
def : Pat<(setugt GPR:$rs1, GPR:$rs2), (SLTU GPR:$rs2, GPR:$rs1)>;
def : Pat<(setuge GPR:$rs1, GPR:$rs2), (XORI (SLTU GPR:$rs1, GPR:$rs2), 1)>;
def : Pat<(setule GPR:$rs1, GPR:$rs2), (XORI (SLTU GPR:$rs2, GPR:$rs1), 1)>;
def : Pat<(setgt GPR:$rs1, GPR:$rs2), (SLT GPR:$rs2, GPR:$rs1)>;
def : Pat<(setge GPR:$rs1, GPR:$rs2), (XORI (SLT GPR:$rs1, GPR:$rs2), 1)>;
def : Pat<(setle GPR:$rs1, GPR:$rs2), (XORI (SLT GPR:$rs2, GPR:$rs1), 1)>;

//== Load/Store Pattern
class AlignedLoad<PatFrag Node>: PatFrag<(ops node:$ptr), (Node node:$ptr), [{
  LoadSDNode *LD = cast<LoadSDNode>(N);
  return LD->getMemoryVT().getSizeInBits()/8 <= LD->getAlignment();
}]>;
class AlignedStore<PatFrag Node>: PatFrag<(ops node:$val, node:$ptr), (Node node:$val, node:$ptr), [{
  StoreSDNode *SD = cast<StoreSDNode>(N);
  return SD->getMemoryVT().getSizeInBits()/8 <= SD->getAlignment();
}]>;

def load_a         : AlignedLoad<load       >;
def sextloadi8_a   : AlignedLoad<sextloadi8 >;
def zextloadi8_a   : AlignedLoad<zextloadi8 >;
def sextloadi16_a  : AlignedLoad<sextloadi16>;
def zextloadi16_a  : AlignedLoad<zextloadi16>;
def  extloadi16_a  : AlignedLoad< extloadi16>;
def sextloadi32_a  : AlignedLoad<sextloadi32>;
def zextloadi32_a  : AlignedLoad<zextloadi32>;
def  extloadi32_a  : AlignedLoad< extloadi32>;
def store_a         : AlignedStore<store        >;
def truncstorei8_a  : AlignedStore<truncstorei8 >;
def truncstorei16_a : AlignedStore<truncstorei16>;
def truncstorei32_a : AlignedStore<truncstorei32>;

let isPseudo = 1, isCodeGenOnly = 1 in {
  def PseudoFI_LA : {{ Xpu }}Inst<(outs GPR:$dst), (ins GPR:$addr, Imm:$offset), "",[]>;
  {% for line in def_load_dags %}
  {{ line }}
  {%- endfor %}
  {%- for line in def_store_dags %}
  {{ line }}
  {%- endfor %}
}

def FIAddr : ComplexPattern<iPTR, 2, "SelectAddrFrameIndexRegImm", [frameindex, add], []>;
def : Pat<(FIAddr (iPTR GPR:$rs1), Imm:$imm),
          (PseudoFI_LA GPR:$rs1, Imm:$imm)>;

def AddrReg      : ComplexPattern<iPTR, 2, "SelectAddrRegImm", [], []>;
{# #}
{%- for line in pat_load_dags %}
{{ line }}
{%- endfor %}
{%- for line in pat_store_dags %}
{{ line }}
{%- endfor %}

//== Branch/Jump Pattern
def PseudoBR: {{ Xpu }}Inst<
  (outs), (ins BrImmS20O1:$imm),
  "",
  [(br bb:$imm)]>,
  PseudoInstExpansion<({{ pseudo_jump_dag }})>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let isBarrier = 1;
  let isBranch = 1;
  let isTerminator = 1;
}

{% for dag in br_dags %}
{{ dag }}
{%- endfor %}

class LongBccPseudo : {{ Xpu }}Inst<
  (outs), (ins {{ long_br_codes['br_dag'] }}),
  "",
  []>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let isBarrier = 1;
  let isBranch = 1;
  let hasSideEffects = 0;
  let mayStore = 0;
  let mayLoad = 0;
  let isAsmParserOnly = 1;
  let hasNoSchedulingInfo = 1;
  let Size = 8;
}

{%- for key in long_br_codes['infos'] %}
def PseudoLong{{ key }} : LongBccPseudo;
{%- endfor %}

def PseudoBRIND: {{ Xpu }}Inst<
  (outs), (ins GPR:$rs1, ImmS12:$imm),
  "",
  []>,
  PseudoInstExpansion<({{ pseudo_jumpind_dag }})>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let isBarrier = 1;
  let isBranch = 1;
  let isIndirectBranch = 1;
  let isTerminator = 1;
}
def : Pat<(brind GPR:$rs1), (PseudoBRIND GPR:$rs1, 0)>;
//def : Pat<(brind (add GPR:$rs1, ImmS12:$imm)), (PseudoBRIND GPR:$rs1, ImmS12:$imm)>;

def SDT_{{ Xpu }}SelectCC : SDTypeProfile<1, 5, [SDTCisSameAs<1, 2>,
                                                 SDTCisSameAs<0, 4>,
                                                 SDTCisSameAs<4, 5>]>;
def SelectCC : SDNode<"{{ Xpu }}ISD::SELECT_CC", SDT_{{ Xpu }}SelectCC, [SDNPInGlue]>;
def Select_GPR : {{ Xpu }}Inst<
  (outs GPR:$dst), (ins GPR:$lhs, GPR:$rhs, ImmS12:$imm, GPR:$truev, GPR:$falsev),
  "",
  [(set GPR:$dst, (SelectCC GPR:$lhs, GPR:$rhs, (i32 imm:$imm), GPR:$truev, GPR:$falsev))]>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let usesCustomInserter = 1;
}
def : Pat<(SelectCC GPR:$lhs, 0, (i32 imm:$imm), GPR:$truev, GPR:$falsev),
          (Select_GPR GPR:$lhs, X0, imm:$imm, GPR:$truev, GPR:$falsev)>;

//=== Function Call Pattern
def SDT_{{ Xpu }}Call : SDTypeProfile<0, -1, [SDTCisVT<0, iPTR>]>;

def {{ xpu }}_call : SDNode<"{{ Xpu }}ISD::CALL", SDT_{{ Xpu }}Call,
  [SDNPHasChain, SDNPOptInGlue, SDNPOutGlue,
  SDNPVariadic]>;

def SDT_CallSeqStart : SDCallSeqStart<[SDTCisVT<0, i32>,
  SDTCisVT<1, i32>]>;
def SDT_CallSeqEnd   : SDCallSeqEnd<[SDTCisVT<0, i32>,
  SDTCisVT<1, i32>]>;

def callseq_start : SDNode<"ISD::CALLSEQ_START", SDT_CallSeqStart,
  [SDNPHasChain, SDNPOutGlue]>;
def callseq_end   : SDNode<"ISD::CALLSEQ_END", SDT_CallSeqEnd,
  [SDNPHasChain, SDNPOptInGlue, SDNPOutGlue]>;

def ADJCALLSTACKDOWN : {{ Xpu }}Inst<(outs), (ins ImmS12:$amt1, ImmS12:$amt2),
  "",
  [(callseq_start timm:$amt1, timm:$amt2)]>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let Defs = [{{ SP }}];
  let Uses = [{{ SP }}];
  let hasSideEffects = 1;
}
def ADJCALLSTACKUP   : {{ Xpu }}Inst<(outs), (ins ImmS12:$amt1, ImmS12:$amt2),
  "",
  [(callseq_end timm:$amt1, timm:$amt2)]>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let Defs = [{{ SP }}];
  let Uses = [{{ SP }}];
  let hasSideEffects = 1;
}

def CallSymbol : AsmOperandClass {
  let Name = "CallSymbol";
  let RenderMethod = "addImmOperands";
  let DiagnosticType = "InvalidCallSymbol";
  let ParserMethod = "parseCallSymbol";
}
def call_symbol : Operand<iPTR> {
  let ParserMatchClass = CallSymbol;
}
def PseudoCALL : {{ Xpu }}Inst<(outs), (ins call_symbol:$func),
  "",
  []>,
  PseudoInstExpansion<({{ pseudo_call_dag }})>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let isCall = 1;
  let Defs = [{{ RA }}];
  //let Size = 8;
}
def : Pat<({{ xpu }}_call tglobaladdr:$func), (PseudoCALL tglobaladdr:$func)>;
def : Pat<({{ xpu }}_call texternalsym:$func), (PseudoCALL texternalsym:$func)>;

def PseudoCALLIndirect : {{ Xpu }}Inst<(outs), (ins GPR:$rs1),
  "",
  [({{ xpu }}_call GPR:$rs1)]>,
  PseudoInstExpansion<({{ pseudo_callind_dag }})>
{
  let isPseudo = 1;
  let isCodeGenOnly = 1;
  let isCall = 1;
  let Defs = [{{ RA }}];
}

//=== Instruction Alias
{% for instr_alias in instr_aliases -%}
def : {{ instr_alias }};
{% endfor %}
