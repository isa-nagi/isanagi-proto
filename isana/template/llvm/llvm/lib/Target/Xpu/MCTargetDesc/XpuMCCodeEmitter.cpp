//===- {{ Xpu }}MCCodeEmitter.cpp - Convert {{ Xpu }} code to machine code -===//

#include "MCTargetDesc/{{ Xpu }}FixupKinds.h"
#include "MCTargetDesc/{{ Xpu }}MCExpr.h"
#include "MCTargetDesc/{{ Xpu }}MCTargetDesc.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/MC/MCCodeEmitter.h"
#include "llvm/MC/MCContext.h"
#include "llvm/MC/MCExpr.h"
#include "llvm/MC/MCFixup.h"
#include "llvm/MC/MCInst.h"
#include "llvm/MC/MCInstBuilder.h"
#include "llvm/MC/MCInstrInfo.h"
#include "llvm/MC/MCRegisterInfo.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/Support/Casting.h"
#include "llvm/Support/Endian.h"
#include "llvm/Support/EndianStream.h"

using namespace llvm;

#define DEBUG_TYPE "mccodeemitter"

namespace {

class {{ Xpu }}MCCodeEmitter : public MCCodeEmitter {
  const MCInstrInfo &MCII;
  const MCRegisterInfo &MRI;
  bool IsBigEndian;
  bool Is64Bit;

public:
  {{ Xpu }}MCCodeEmitter(const MCInstrInfo &mcii, const MCRegisterInfo &mri,
                   bool IsBigEndian, bool Is64Bit)
      : MCII(mcii), MRI(mri), IsBigEndian(IsBigEndian), Is64Bit(Is64Bit) { }
  {{ Xpu }}MCCodeEmitter(const {{ Xpu }}MCCodeEmitter &) = delete;
  void operator=(const {{ Xpu }}MCCodeEmitter &) = delete;
  ~{{ Xpu }}MCCodeEmitter() override = default;

  // getBinaryCodeForInstr - TableGen'erated function for getting the
  // binary encoding for an instruction.
  uint64_t getBinaryCodeForInstr(const MCInst &MI,
      SmallVectorImpl<MCFixup> &Fixups,
      const MCSubtargetInfo &STI) const;

  // getMachineOpValue - Return binary encoding of operand. If the machin
  // operand requires relocation, record the relocation and return zero.
  unsigned getMachineOpValue(const MCInst &MI, const MCOperand &MO,
    SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &STI) const;

  template <unsigned S>
  unsigned getImmOpValueRShift(
    const MCInst &MI, unsigned OpNo,
    SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &STI) const;

  // uint64_t getMemoryOpValue(const MCInst &MI, unsigned Op,
  //   SmallVectorImpl<MCFixup> &Fixups,
  //   const MCSubtargetInfo &STI) const;

  void encodeInstruction(const MCInst &MI, SmallVectorImpl<char> &CB,
    SmallVectorImpl<MCFixup> &Fixups,
    const MCSubtargetInfo &STI) const override;

  void expandFunctionCall(const MCInst &MI, SmallVectorImpl<char> &CB,
                          SmallVectorImpl<MCFixup> &Fixups,
                          const MCSubtargetInfo &STI) const;

  void expandLongBranch(const MCInst &MI, SmallVectorImpl<char> &CB,
                        SmallVectorImpl<MCFixup> &Fixups,
                        const MCSubtargetInfo &STI) const;
};

} // end anonymous namespace

MCCodeEmitter *
llvm::create{{ Xpu }}MCCodeEmitter(
  const MCInstrInfo &MCII,
  MCContext &Ctx
)
{
  return new {{ Xpu }}MCCodeEmitter(MCII, *Ctx.getRegisterInfo(), false, false);
}

void
{{ Xpu }}MCCodeEmitter::expandFunctionCall(
  const MCInst &MI,
  SmallVectorImpl<char> &CB,
  SmallVectorImpl<MCFixup> &Fixups,
  const MCSubtargetInfo &STI
) const {
  MCInst TmpInst;
  MCOperand Func;
  MCRegister Ra;
  uint32_t Binary;

  if (MI.getOpcode() == {{ Xpu }}::PseudoCALL) {
    Func = MI.getOperand(0);
    Ra = {{ Xpu }}::{{ RA }};
  }

  assert(Func.isExpr() && "Expected expression");

  const MCExpr *CallExpr = Func.getExpr();

  if ({% if mc_longcall_codes %}1{% else %}0{% endif %}) {
    // long jump
    //           | --RISC-V spec--
    // call func | auipc x1, <expr:sym=func>
    //           |   + fixup:call
    //           | jalr x1, x1, 0
    {%- for line in mc_longcall_codes %}
    {{ line }}
    {%- endfor %}
  } else {
    // short jump
    //           | --RISC-V spec--
    // call func | jal x1, <expr:sym=func>
    //           |   + fixup:call
    {%- for line in mc_call_codes %}
    {{ line }}
    {%- endfor %}
  }
}

static unsigned getInvertedBranchOp(unsigned BrOp) {
  switch (BrOp) {
  default:
    llvm_unreachable("Unexpected branch opcode!");
  {%- for key, val in long_br_codes['infos'].items() %}
  case {{ Xpu }}::PseudoLong{{ key }}:
    return {{ Xpu }}::{{ val['inv'] }};
  {%- endfor %}
  }
}

void
{{ Xpu }}MCCodeEmitter::expandLongBranch(
  const MCInst &MI,
  SmallVectorImpl<char> &CB,
  SmallVectorImpl<MCFixup> &Fixups,
  const MCSubtargetInfo &STI
) const {
  // branch
  //   br src1, src2, dstimm2
  //   dstimm1:
  //     ...
  //   dstimm2:
  //     ...
  //
  // long branch
  //   brInv src1, src2, 8(=dstimm1)
  //   jal x0, dstimm2
  //   dstimm1:
  //     ...
  //   dstimm2:
  //     ...

  {%- for line in long_br_codes['codes2'] %}
  {{ line }}
  {%- endfor %}
  unsigned Opcode = MI.getOpcode();
  // bool IsEqTest =
  //     Opcode == {{ Xpu }}::PseudoLongBNE || Opcode == {{ Xpu }}::PseudoLongBEQ;

  uint32_t Offset;
  // if (UseCompressedBr) {
  // } else
  {
    unsigned InvOpc = getInvertedBranchOp(Opcode);
    MCInst TmpInst =
        {{ long_br_codes['br_mcinst'] }}
    uint32_t Binary = getBinaryCodeForInstr(TmpInst, Fixups, STI);
    support::endian::write(CB, Binary, llvm::endianness::little);
    Offset = 4;
  }

  // Emit an unconditional jump to the destination.
  MCInst TmpInst =
        {{ long_br_codes['jump_mcinst'] }}
  uint32_t Binary = getBinaryCodeForInstr(TmpInst, Fixups, STI);
  support::endian::write(CB, Binary, llvm::endianness::little);

  Fixups.clear();
  if (SrcSymbol.isExpr()) {
    Fixups.push_back(MCFixup::create(Offset, SrcSymbol.getExpr(),
                                     MCFixupKind({{ long_br_codes['jump_fixup'] }}),
                                     MI.getLoc()));
  }
}

unsigned
{{ Xpu }}MCCodeEmitter::getMachineOpValue(
  const MCInst &MI,
  const MCOperand &MO,
  SmallVectorImpl<MCFixup> &Fixups,
  const MCSubtargetInfo &STI
) const
{
  if (MO.isReg())
    return MRI.getEncodingValue(MO.getReg());
  if (MO.isImm())
    return static_cast<unsigned>(MO.getImm());

  // llvm_unreachable("Unhandled expression!");
  const MCExpr *Expr = MO.getExpr();
  MCExpr::ExprKind Kind = Expr->getKind();
  {{ Xpu }}::Fixups FixupKind = {{ Xpu }}::fixup_{{ xpu }}_invalid;
  if (Kind == MCExpr::Target) {
    const {{ Xpu }}MCExpr *XExpr = cast<{{ Xpu }}MCExpr>(Expr);
    switch (XExpr->getKind()) {
    default:
      break;
    case {{ Xpu }}MCExpr::VK_{{ Xpu }}_None:
    case {{ Xpu }}MCExpr::VK_{{ Xpu }}_Invalid:
      llvm_unreachable("Unhandled fixup kind!");
    case {{ Xpu }}MCExpr::VK_{{ Xpu }}_CALL:
      FixupKind = {{ Xpu }}::fixup_{{ xpu }}_call;
      break;
    case {{ Xpu }}MCExpr::VK_{{ Xpu }}_SYMBOL:
      {
        unsigned Opcode = MI.getOpcode();
        switch (Opcode) {
        default:
          break;
        {% for fx in fixup_relocs -%}
        {% for instr in fx.instrs -%}
        case {{ Xpu }}::{{ instr.__name__.upper() }}:
        {% endfor %}  FixupKind = {{ Xpu }}::{{ fx.name_enum}};
          break;
        {% endfor -%}
        }
      }
      break;
    }
  } else if ((Kind == MCExpr::SymbolRef &&
                 cast<MCSymbolRefExpr>(Expr)->getKind() ==
                     MCSymbolRefExpr::VK_None) ||
             Kind == MCExpr::Binary) {
      unsigned Opcode = MI.getOpcode();
      switch (Opcode) {
      default:
        break;
      {% for fx in fixup_relocs -%}
      {% for instr in fx.instrs -%}
      case {{ Xpu }}::{{ instr.__name__.upper() }}:
      {% endfor %}  FixupKind = {{ Xpu }}::{{ fx.name_enum}};
        break;
      {% endfor -%}
      }
  }

  assert(FixupKind != {{ Xpu }}::fixup_{{ xpu }}_invalid && "Unhandled expression!");

  Fixups.push_back(
      MCFixup::create(0, Expr, MCFixupKind(FixupKind), MI.getLoc()));
  return 0;
}

template <unsigned S>
unsigned
{{ Xpu }}MCCodeEmitter::getImmOpValueRShift(
  const MCInst &MI, unsigned OpNo,
  SmallVectorImpl<MCFixup> &Fixups,
  const MCSubtargetInfo &STI
) const {
  const MCOperand &MO = MI.getOperand(OpNo);

  if (MO.isImm()) {
    unsigned Res = MO.getImm();
    assert((Res & ((1 << S) - 1)) == 0 && "LSB is non-zero");
    return Res >> S;
  }
  return getMachineOpValue (MI, MO, Fixups, STI);
}

void
{{ Xpu }}MCCodeEmitter::encodeInstruction(
  const MCInst &MI,
  SmallVectorImpl<char> &CB,
  SmallVectorImpl<MCFixup> &Fixups,
  const MCSubtargetInfo &STI
) const
{
  const unsigned Opcode = MI.getOpcode();
  const MCInstrDesc &Desc = MCII.get(Opcode);
  unsigned Size = Desc.getSize();

  switch (MI.getOpcode()) {
  default:
    break;
  case {{ Xpu }}::PseudoCALL:
    expandFunctionCall(MI, CB, Fixups, STI);
    return;
  {%- for key in long_br_codes['infos'] %}
  case {{ Xpu }}::PseudoLong{{ key }}:
  {%- endfor %}
    expandLongBranch(MI, CB, Fixups, STI);
    return;
  }

  // Get instruction encoding and emit it
  auto Endian = IsBigEndian ? llvm::endianness::big : llvm::endianness::little;
  switch (Size) {
  case 2: {
    uint16_t Binary = getBinaryCodeForInstr(MI, Fixups, STI);
    support::endian::write<uint16_t>(CB, Binary, Endian);
    break;
  }
  case 4: {
    uint32_t Binary = getBinaryCodeForInstr(MI, Fixups, STI);
    support::endian::write<uint32_t>(CB, Binary, Endian);
    break;
  }
  case 8: {
    uint64_t Binary = getBinaryCodeForInstr(MI, Fixups, STI);
    support::endian::write<uint64_t>(CB, Binary, Endian);
    break;
  }
  default: {
    llvm_unreachable("Unhandled encodeInstruction length!");
  }
  }
}

#include "{{ Xpu }}GenMCCodeEmitter.inc"
