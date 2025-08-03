//===- {{ Xpu }}MCExpr.cpp - {{ Xpu }} specific MC expression classes -===//

#include "{{ Xpu }}FixupKinds.h"
#include "{{ Xpu }}MCExpr.h"
#include "llvm/BinaryFormat/ELF.h"
#include "llvm/MC/MCAssembler.h"
#include "llvm/MC/MCContext.h"
#include "llvm/MC/MCStreamer.h"
#include "llvm/MC/MCSymbolELF.h"
#include "llvm/Support/Casting.h"

using namespace llvm;

#define DEBUG_TYPE "{{ xpu }}-mc-expr"

const {{ Xpu }}MCExpr *{{ Xpu }}MCExpr::create(const MCExpr *Expr, VariantKind Kind,
                                     MCContext &Ctx) {
  return new (Ctx) {{ Xpu }}MCExpr(Kind, Expr);
}

StringRef {{ Xpu }}MCExpr::getVariantKindName(VariantKind Kind) {
  switch (Kind) {
  default:
    llvm_unreachable("Invalid ELF symbol kind");
  case VK_{{ Xpu }}_None:
    return "";
  case VK_{{ Xpu }}_CALL:  // TODO fix it
    return "";
  case VK_{{ Xpu }}_SYMBOL:
    return "";
  }
}

void {{ Xpu }}MCExpr::visitUsedExpr(MCStreamer &Streamer) const {
  Streamer.visitUsedExpr(*getSubExpr());
}

void {{ Xpu }}MCExpr::printImpl(raw_ostream &OS, const MCAsmInfo *MAI) const {
  Expr->print(OS, MAI);
  OS << getVariantKindName(getKind());
}

void {{ Xpu }}MCExpr::fixELFSymbolsInTLSFixups(MCAssembler &Asm) const {
  switch (getKind()) {
  default:
    return;
  // case VK_{{ Xpu }}_TLSLE:
  // case VK_{{ Xpu }}_TLSIE:
  // case VK_{{ Xpu }}_TLSGD:
  //   break;
  }

  // fixELFSymbolsInTLSFixupsImpl(getSubExpr(), Asm);
}

bool {{ Xpu }}MCExpr::evaluateAsRelocatableImpl(MCValue &Res, const MCAssembler *Asm,
                                           const MCFixup *Fixup) const {
  if (!getSubExpr()->evaluateAsRelocatable(Res, Asm, Fixup))
    return false;

  // Some custom fixup types are not valid with symbol difference expressions
  if (Res.getSymA() && Res.getSymB()) {
    switch (getKind()) {
    default:
      return true;
    // case VK_{{ Xpu }}_GOT:
    // case VK_{{ Xpu }}_GOTPC:
    // case VK_{{ Xpu }}_GOTOFF:
    // case VK_{{ Xpu }}_PLT:
    // case VK_{{ Xpu }}_TLSIE:
    //   return false;
    }
  }

  return true;
}

bool {{ Xpu }}MCExpr::evaluateAsConstant(int64_t &Res) const
{
  MCValue Value;

  if (Kind == VK_{{ Xpu }}_CALL)  // TODO fix it
    return false;

  if (!getSubExpr()->evaluateAsRelocatable(Value, nullptr, nullptr))
    return false;

  if (!Value.isAbsolute())
    return false;

  // Res = evaluateAsInt64(Value.getConstant());
  Res = Value.getConstant();
  return true;
}
