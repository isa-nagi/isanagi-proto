//===- {{ Xpu }}InstPrinter.h - Convert {{ Xpu }} MCInst to asm syntax -===//

#ifndef LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}INSTPRINTER_H
#define LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}INSTPRINTER_H

#include "MCTargetDesc/{{ Xpu }}MCTargetDesc.h"
#include "llvm/MC/MCInstPrinter.h"

namespace llvm {

class {{ Xpu }}InstPrinter : public MCInstPrinter {
public:
  {{ Xpu }}InstPrinter(const MCAsmInfo &MAI, const MCInstrInfo &MII,
                   const MCRegisterInfo &MRI)
      : MCInstPrinter(MAI, MII, MRI) {}

  bool applyTargetSpecificCLOption(StringRef Opt) override;

  void printInst(const MCInst *MI, uint64_t Address, StringRef Annot,
                 const MCSubtargetInfo &STI, raw_ostream &O) override;
  void printRegName(raw_ostream &O, MCRegister Reg) const override;

  void printOperand(const MCInst *MI, unsigned OpNo,
                    const MCSubtargetInfo &STI,
                    raw_ostream &O, const char *Modifier = nullptr);
  void printOperand(const MCInst *MI, unsigned Address, unsigned OpNo,
                    const MCSubtargetInfo &STI,
                    raw_ostream &O, const char *Modifier = nullptr) {
    printOperand(MI, OpNo, STI, O, Modifier);
  }
  {% for asmopcls in asm_operand_clss -%}
  void print{{ asmopcls.name }}(const MCInst *MI, unsigned OpNo,
          const MCSubtargetInfo &STI, raw_ostream &O);
  {% endfor %}
  // Autogenerated by tblgen.
  std::pair<const char *, uint64_t> getMnemonic(const MCInst *MI) override;
  void printInstruction(const MCInst *MI, uint64_t Address,
                        const MCSubtargetInfo &STI, raw_ostream &O);
  bool printAliasInstr(const MCInst *MI, uint64_t Address,
                       const MCSubtargetInfo &STI, raw_ostream &O);
  void printCustomAliasOperand(const MCInst *MI, uint64_t Address,
                               unsigned OpIdx, unsigned PrintMethodIdx,
                               const MCSubtargetInfo &STI, raw_ostream &O);
  static const char *getRegisterName(MCRegister Reg);
  static const char *getRegisterName(MCRegister Reg, unsigned AltIdx);
};
} // namespace llvm

#endif
