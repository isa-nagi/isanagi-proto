//===- {{ Xpu }}ELFObjectWriter.cpp - {{ Xpu }} ELF Writer -===//

#include "{{ Xpu }}FixupKinds.h"
#include "{{ Xpu }}MCExpr.h"
#include "{{ Xpu }}MCTargetDesc.h"
#include "llvm/MC/MCContext.h"
#include "llvm/MC/MCELFObjectWriter.h"
#include "llvm/MC/MCObjectWriter.h"
// #include "llvm/MC/MCSymbol.h"
#include "llvm/MC/MCValue.h"

#define DEBUG_TYPE "{{ xpu }}-elf-object-writer"

using namespace llvm;

namespace {

class {{ Xpu }}ELFObjectWriter : public MCELFObjectTargetWriter {
public:
  {{ Xpu }}ELFObjectWriter(uint8_t OSABI = 0)
      : MCELFObjectTargetWriter(false, OSABI, ELF::EM_{{ XPU }}, true){};
  ~{{ Xpu }}ELFObjectWriter() {}

  unsigned getRelocType(MCContext &Ctx, const MCValue &Target,
                        const MCFixup &Fixup, bool IsPCRel) const override;
};

} // namespace

unsigned
{{ Xpu }}ELFObjectWriter::getRelocType(
  MCContext &Ctx,
  const MCValue &Target,
  const MCFixup &Fixup,
  bool IsPCRel
) const
{
  const MCExpr *Expr = Fixup.getValue();
  // Determine the type of the relocation
  unsigned Kind = Fixup.getTargetKind();
  // MCSymbolRefExpr::VariantKind Modifier = Target.getAccessVariant();

  if (IsPCRel) {
    switch (Kind) {
    default:
      LLVM_DEBUG(dbgs() << "Unknown Kind1  = " << Kind);
      Ctx.reportError(Fixup.getLoc(), "Unsupported relocation type");
      return ELF::R_CKCORE_NONE;
    case FK_PCRel_4:
      return ELF::R_CKCORE_PCREL32;
    case {{ Xpu }}::{{ fixup_call.name_enum }}:
      return ELF::R_{{ XPU }}_CALL;
    {% for fx in fixups_pc_rel -%}
    case {{ Xpu }}::{{ fx.name_enum }}:
      return ELF::R_{{ XPU }}_{{ fx.name.upper() }};
    {% endfor %}
    }
  }

  switch (Kind) {
  default:
    LLVM_DEBUG(dbgs() << "Unknown Kind2  = " << Kind);
    Ctx.reportError(Fixup.getLoc(), "Unsupported relocation type");
    return ELF::R_CKCORE_NONE;
  case FK_Data_1:
    Ctx.reportError(Fixup.getLoc(), "1-byte data relocations not supported");
    return ELF::R_CKCORE_NONE;
  case FK_Data_2:
    Ctx.reportError(Fixup.getLoc(), "2-byte data relocations not supported");
    return ELF::R_CKCORE_NONE;
  case FK_Data_4:
    if (Expr->getKind() == MCExpr::Target) {
      auto TK = cast<{{ Xpu }}MCExpr>(Expr)->getKind();
      // if (TK == {{ Xpu }}MCExpr::VK_{{ Xpu }}_ADDR)
      //   return ELF::R_CKCORE_ADDR32;
      if (TK == {{ Xpu }}MCExpr::VK_{{ Xpu }}_None)
        return ELF::R_CKCORE_ADDR32;
      return ELF::R_{{ XPU }}_32;
    }
    // else {
    //   switch (Modifier) {
    //   default:
    //     Ctx.reportError(Fixup.getLoc(),
    //                     "invalid fixup for 4-byte data relocation");
    //     return ELF::R_CKCORE_NONE;
    //   case MCSymbolRefExpr::VK_None:
    //     return ELF::R_CKCORE_ADDR32;
    //   }
    // }
    // return ELF::R_CKCORE_NONE;
    return ELF::R_{{ XPU }}_32;
  case FK_Data_8:
    return ELF::R_{{ XPU }}_64;
  case {{ Xpu }}::{{ fixup_call.name_enum }}:
    return ELF::R_{{ XPU }}_CALL;
  {% for fx in fixup_relocs -%}
  case {{ Xpu }}::{{ fx.name_enum }}:
    return ELF::R_{{ XPU }}_{{ fx.name.upper() }};
  {% endfor %}
  }
}

std::unique_ptr<MCObjectTargetWriter>
llvm::create{{ Xpu }}ELFObjectWriter(
)
{
  return std::make_unique<{{ Xpu }}ELFObjectWriter>();
}
