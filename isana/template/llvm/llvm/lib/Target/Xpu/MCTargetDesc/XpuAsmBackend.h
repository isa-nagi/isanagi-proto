//===- {{ Xpu }}AsmBackend.h - {{ Xpu }} Assembler Backend -===//

#ifndef LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}ASMBACKEND_H
#define LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}ASMBACKEND_H

#include "MCTargetDesc/{{ Xpu }}FixupKinds.h"
#include "llvm/MC/MCAsmBackend.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/MC/MCTargetOptions.h"

namespace llvm {

class {{ Xpu }}AsmBackend : public MCAsmBackend {

public:
  {{ Xpu }}AsmBackend(const MCSubtargetInfo &STI, const MCTargetOptions &OP)
      : MCAsmBackend(llvm::endianness::little) {}

  unsigned int getNumFixupKinds() const override {
    return {{ Xpu }}::NumTargetFixupKinds;
  }

  void applyFixup(const MCAssembler &Asm, const MCFixup &Fixup,
                  const MCValue &Target, MutableArrayRef<char> Data,
                  uint64_t Value, bool IsResolved,
                  const MCSubtargetInfo *STI) const override;

  const MCFixupKindInfo &getFixupKindInfo(MCFixupKind Kind) const override;

  // No need to implement if fixupNeedsRelaxationAdvanced is used.
  // bool fixupNeedsRelaxation(const MCFixup &Fixup,
  //                           uint64_t Value) const override;

  void relaxInstruction(MCInst &Inst,
                        const MCSubtargetInfo &STI) const override;

  bool mayNeedRelaxation(const MCInst &Inst,
                         const MCSubtargetInfo &STI) const override;

  bool fixupNeedsRelaxationAdvanced(const MCAssembler &Asm,
                                    const MCFixup &Fixup, bool Resolved,
                                    uint64_t Value,
                                    const MCRelaxableFragment *DF,
                                    const bool WasForced) const override;

  bool writeNopData(raw_ostream &OS, uint64_t Count,
                    const MCSubtargetInfo *STI) const override;

  bool shouldForceRelocation(const MCAssembler &Asm, const MCFixup &Fixup,
                             const MCValue &Target,
                             const MCSubtargetInfo *STI) override;

  std::unique_ptr<MCObjectTargetWriter>
  createObjectTargetWriter() const override;
};
} // namespace llvm

#endif // LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}ASMBACKEND_H
