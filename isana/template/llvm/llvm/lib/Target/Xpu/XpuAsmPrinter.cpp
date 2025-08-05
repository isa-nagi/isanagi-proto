//===-- {{ Xpu }}AsmPrinter.cpp - {{ Xpu }} LLVM assembly writer --===//

#include "{{ Xpu }}.h"
#include "{{ Xpu }}InstrInfo.h"
#include "{{ Xpu }}TargetMachine.h"
#include "MCTargetDesc/{{ Xpu }}BaseInfo.h"
#include "MCTargetDesc/{{ Xpu }}InstPrinter.h"
#include "MCTargetDesc/{{ Xpu }}MCExpr.h"
// #include "MCTargetDesc/{{ Xpu }}TargetStreamer.h"
#include "TargetInfo/{{ Xpu }}TargetInfo.h"
#include "llvm/CodeGen/AsmPrinter.h"
#include "llvm/CodeGen/MachineConstantPool.h"
#include "llvm/CodeGen/MachineFunctionPass.h"
#include "llvm/CodeGen/MachineInstr.h"
#include "llvm/CodeGen/MachineModuleInfo.h"
#include "llvm/IR/Module.h"
#include "llvm/MC/MCAsmInfo.h"
#include "llvm/MC/MCInst.h"
#include "llvm/MC/MCStreamer.h"
#include "llvm/MC/MCSymbol.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

#define DEBUG_TYPE "asm-printer"

namespace {
class {{ Xpu }}AsmPrinter : public AsmPrinter {
public:
  explicit {{ Xpu }}AsmPrinter(TargetMachine &TM,
                         std::unique_ptr<MCStreamer> Streamer)
      : AsmPrinter(TM, std::move(Streamer)) {}

  StringRef getPassName() const override { return "{{ Xpu }} Assembly Printer"; }
  // bool doInitialization(Module &M) override;
  // bool doFinalization(Module &M) override;

  // bool runOnMachineFunction(MachineFunction &MF) override;

  void emitInstruction(const MachineInstr *MI) override;

  bool PrintAsmOperand(const MachineInstr *MI, unsigned OpNo,
                       const char *ExtraCode, raw_ostream &O) override;
  // bool PrintAsmMemoryOperand(const MachineInstr *MI, unsigned OpNum,
  //                            const char *ExtraCode, raw_ostream &O) override;

  // void emitStartOfAsmFile(Module &M) override;
  // void emitEndOfAsmFile(Module &M) override;

  // void emitFunctionEntryLabel() override;

  bool lowerPseudoInstExpansion(const MachineInstr *MI, MCInst &Inst);
  bool lowerOperand(const MachineOperand &MO, MCOperand &MCOp) const;
  bool lowerToMCInst(const MachineInstr *MI, MCInst &OutMI);
};
} // namespace

// Simple pseudo-instructions have their lowering (with expansion to real
// instructions) auto-generated.
#include "{{ Xpu }}GenMCPseudoLowering.inc"

void {{ Xpu }}AsmPrinter::emitInstruction(const MachineInstr *MI) {
  {{ Xpu }}_MC::verifyInstructionPredicates(MI->getOpcode(),
                                      getSubtargetInfo().getFeatureBits());

  // Do any auto-generated pseudo lowerings.
  if (MCInst OutInst; lowerPseudoInstExpansion(MI, OutInst)) {
    EmitToStreamer(*OutStreamer, OutInst);
    return;
  }

  MCInst OutInst;
  if (!lowerToMCInst(MI, OutInst))
    EmitToStreamer(*OutStreamer, OutInst);
}

bool {{ Xpu }}AsmPrinter::PrintAsmOperand(
  const MachineInstr *MI, unsigned OpNo,
  const char *ExtraCode, raw_ostream &OS
) {
  // First try the generic code, which knows about modifiers like 'c' and 'n'.
  if (!AsmPrinter::PrintAsmOperand(MI, OpNo, ExtraCode, OS))
    return false;

  const MachineOperand &MO = MI->getOperand(OpNo);
  if (ExtraCode && ExtraCode[0]) {
    if (ExtraCode[1] != 0)
      return true; // Unknown modifier.

    switch (ExtraCode[0]) {
    default:
      return true; // Unknown modifier.
    case 'z':      // Print zero register if zero, regular printing otherwise.
      if (MO.isImm() && MO.getImm() == 0) {
        OS << {{ Xpu }}InstPrinter::getRegisterName({{ Xpu }}::{{ REG0 }});
        return false;
      }
      break;
    case 'i': // Literal 'i' if operand is not a register.
      if (!MO.isReg())
        OS << 'i';
      return false;
    }
  }

  switch (MO.getType()) {
  case MachineOperand::MO_Immediate:
    OS << MO.getImm();
    return false;
  case MachineOperand::MO_Register:
    OS << {{ Xpu }}InstPrinter::getRegisterName(MO.getReg());
    return false;
  case MachineOperand::MO_GlobalAddress:
    PrintSymbolOperand(MO, OS);
    return false;
  case MachineOperand::MO_BlockAddress: {
    MCSymbol *Sym = GetBlockAddressSymbol(MO.getBlockAddress());
    Sym->print(OS, MAI);
    return false;
  }
  default:
    break;
  }

  return true;
}

static MCOperand lowerSymbolOperand(const MachineOperand &MO, MCSymbol *Sym,
                                    const AsmPrinter &AP) {
  MCContext &Ctx = AP.OutContext;
  {{ Xpu }}MCExpr::VariantKind Kind;

  switch(MO.getTargetFlags()) {
  default:
    llvm_unreachable("Unknown target flag on GV operand");
  case {{ Xpu }}II::MO_None:
    Kind = {{ Xpu }}MCExpr::VK_{{ Xpu }}_None;
    break;
  {%- for expr in asm_call_exprs + asm_other_exprs %}
  case {{ Xpu }}II::MO_{{ expr.name.upper() }}:
    Kind = {{ Xpu }}MCExpr::VK_{{ Xpu }}_{{ expr.name.upper() }};
    break;
  {%- endfor %}
  }

  const MCExpr *ME =
      MCSymbolRefExpr::create(Sym, MCSymbolRefExpr::VK_None, Ctx);

  if (!MO.isJTI() && !MO.isMBB() && MO.getOffset())
    ME = MCBinaryExpr::createAdd(
        ME, MCConstantExpr::create(MO.getOffset(), Ctx), Ctx);

  if (Kind != {{ Xpu }}MCExpr::VK_{{ Xpu }}_None)
    ME = {{ Xpu }}MCExpr::create(ME, Kind, Ctx);
  return MCOperand::createExpr(ME);
}

bool {{ Xpu }}AsmPrinter::lowerOperand(const MachineOperand &MO,
                                   MCOperand &MCOp) const {
  switch (MO.getType()) {
  default:
    report_fatal_error("lowerOperand: unknown operand type");
  case MachineOperand::MO_Register:
    // Ignore all implicit register operands.
    if (MO.isImplicit())
      return false;
    MCOp = MCOperand::createReg(MO.getReg());
    break;
  case MachineOperand::MO_RegisterMask:
    // Regmasks are like implicit defs.
    return false;
  case MachineOperand::MO_Immediate:
    MCOp = MCOperand::createImm(MO.getImm());
    break;
  case MachineOperand::MO_MachineBasicBlock:
    MCOp = lowerSymbolOperand(MO, MO.getMBB()->getSymbol(), *this);
    break;
  case MachineOperand::MO_GlobalAddress:
    MCOp = lowerSymbolOperand(MO, getSymbolPreferLocal(*MO.getGlobal()), *this);
    break;
  case MachineOperand::MO_BlockAddress:
    MCOp = lowerSymbolOperand(MO, GetBlockAddressSymbol(MO.getBlockAddress()),
                              *this);
    break;
  case MachineOperand::MO_ExternalSymbol:
    MCOp = lowerSymbolOperand(MO, GetExternalSymbolSymbol(MO.getSymbolName()),
                              *this);
    break;
  case MachineOperand::MO_ConstantPoolIndex:
    MCOp = lowerSymbolOperand(MO, GetCPISymbol(MO.getIndex()), *this);
    break;
  case MachineOperand::MO_JumpTableIndex:
    MCOp = lowerSymbolOperand(MO, GetJTISymbol(MO.getIndex()), *this);
    break;
  case MachineOperand::MO_MCSymbol:
    MCOp = lowerSymbolOperand(MO, MO.getMCSymbol(), *this);
    break;
  }
  return true;
}

bool {{ Xpu }}AsmPrinter::lowerToMCInst(const MachineInstr *MI, MCInst &OutMI) {
  OutMI.setOpcode(MI->getOpcode());

  for (const MachineOperand &MO : MI->operands()) {
    MCOperand MCOp;
    if (lowerOperand(MO, MCOp))
      OutMI.addOperand(MCOp);
  }

  return false;
}

// Force static initialization.
extern "C" LLVM_EXTERNAL_VISIBILITY void LLVMInitialize{{ Xpu }}AsmPrinter() {
  RegisterAsmPrinter<{{ Xpu }}AsmPrinter> Z(getThe{{ Xpu }}32leTarget());
  RegisterAsmPrinter<{{ Xpu }}AsmPrinter> Y(getThe{{ Xpu }}32beTarget());
  RegisterAsmPrinter<{{ Xpu }}AsmPrinter> X(getThe{{ Xpu }}64leTarget());
  RegisterAsmPrinter<{{ Xpu }}AsmPrinter> W(getThe{{ Xpu }}64beTarget());
}
