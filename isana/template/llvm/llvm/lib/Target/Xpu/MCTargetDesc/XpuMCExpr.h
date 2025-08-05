//===- {{ Xpu }}MCExpr.h - {{ Xpu }} specific MC expression classes -===//

#ifndef LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}MCEXPR_H
#define LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}MCEXPR_H

#include "llvm/MC/MCExpr.h"
#include "llvm/MC/MCValue.h"

namespace llvm {

class {{ Xpu }}MCExpr : public MCTargetExpr {
public:
  enum VariantKind {
    VK_{{ Xpu }}_None,
    {%- for expr in asm_call_exprs + asm_other_exprs %}
    VK_{{ Xpu }}_{{ expr.name.upper() }},
    {%- endfor %}
    VK_{{ Xpu }}_Invalid
  };

private:
  const VariantKind Kind;
  const MCExpr *Expr;

  explicit {{ Xpu }}MCExpr(VariantKind Kind, const MCExpr *Expr)
      : Kind(Kind), Expr(Expr) {}

public:
  static const {{ Xpu }}MCExpr *create(const MCExpr *Expr, VariantKind Kind,
                                  MCContext &Ctx);

  // Returns the kind of this expression.
  VariantKind getKind() const { return Kind; }

  // Returns the child of this expression.
  const MCExpr *getSubExpr() const { return Expr; }

  void printImpl(raw_ostream &OS, const MCAsmInfo *MAI) const override;

  bool evaluateAsRelocatableImpl(MCValue &Res, const MCAssembler *Asm,
                                 const MCFixup *Fixup) const override;
  bool evaluateAsConstant(int64_t &Res) const;

  void visitUsedExpr(MCStreamer &Streamer) const override;

  MCFragment *findAssociatedFragment() const override {
    return getSubExpr()->findAssociatedFragment();
  }

  void fixELFSymbolsInTLSFixups(MCAssembler &Asm) const override;

  static bool classof(const MCExpr *E) {
    return E->getKind() == MCExpr::Target;
  }

  static VariantKind getVariantKindForName(StringRef name);
  static StringRef getVariantKindName(VariantKind Kind);
};
} // end namespace llvm

#endif
