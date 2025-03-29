//===- {{ Xpu }}InstPrinter.cpp - Convert {{ Xpu }} MCInst to asm syntax -===//

#include "{{ Xpu }}InstPrinter.h"
// #include "{{ Xpu }}BaseInfo.h"
// #include "{{ Xpu }}MCExpr.h"
#include "llvm/MC/MCAsmInfo.h"
#include "llvm/MC/MCExpr.h"
#include "llvm/MC/MCInst.h"
#include "llvm/MC/MCInstPrinter.h"
#include "llvm/MC/MCRegisterInfo.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/MC/MCSymbol.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/ErrorHandling.h"
#include "llvm/Support/FormattedStream.h"
using namespace llvm;

#define DEBUG_TYPE "asm-printer"

// Include the auto-generated portion of the assembly writer.
#define PRINT_ALIAS_INSTR
#include "{{ Xpu }}GenAsmWriter.inc"

static bool ArchRegNames;

bool
{{ Xpu }}InstPrinter::applyTargetSpecificCLOption(
  StringRef Opt
)
{
  if (Opt == "no-aliases") {
    PrintAliases = false;
    return true;
  }
  if (Opt == "numeric") {
    ArchRegNames = true;
    return true;
  }

  return false;
}

void
{{ Xpu }}InstPrinter::printInst(
  const MCInst *MI, uint64_t Address,
  StringRef Annot, const MCSubtargetInfo &STI,
  raw_ostream &O
)
{
  if (!printAliasInstr(MI, Address, STI, O))
    printInstruction(MI, Address, STI, O);
  printAnnotation(O, Annot);
}

void
{{ Xpu }}InstPrinter::printRegName(
  raw_ostream &O, MCRegister Reg
) const
{
  markup(O, Markup::Register) << getRegisterName(Reg);
}

void
{{ Xpu }}InstPrinter::printOperand(
  const MCInst *MI, unsigned OpNo,
  const MCSubtargetInfo &STI,
  raw_ostream &O,
  const char *Modifier
)
{
  assert((Modifier == nullptr || Modifier[0] == 0) && "No modifiers supported");
  const MCOperand &MO = MI->getOperand(OpNo);

  if (MO.isReg()) {
    printRegName(O, MO.getReg());
    return;
  }

  if (MO.isImm()) {
    markup(O, Markup::Immediate) << formatImm(MO.getImm());
    return;
  }

  assert(MO.isExpr() && "Unknown operand kind in printOperand");
  MO.getExpr()->print(O, &MAI);
}

{% for asmopcls in asm_operand_clss -%}
void
{{ Xpu }}InstPrinter::print{{ asmopcls.name }}(
  const MCInst *MI,
  unsigned OpNo,
  const MCSubtargetInfo &STI,
  raw_ostream &O
)
{
  const MCOperand &MO = MI->getOperand(OpNo);

  if (MO.isImm()) {
    uint64_t imm = MO.getImm();
    switch (imm) {
    default:
      break;
    {% for k, v in asmopcls.enums.items() -%}
      case {{ k }}:
        markup(O, Markup::Immediate) << "{{ v }}";
        return;
    {% endfor -%}
    }
  }

  assert(MO.isExpr() && "Unknown operand kind in print{{ asmopcls.name }}");
  MO.getExpr()->print(O, &MAI);
}
{% endfor %}

const char *
{{ Xpu }}InstPrinter::getRegisterName(MCRegister Reg) {
  return getRegisterName(Reg, ArchRegNames ? {{ Xpu }}::NoRegAltName
                                           : {{ Xpu }}::ABIRegAltName);
}
