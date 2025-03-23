//===- {{ Xpu }}MCTargetDesc.cpp - {{ Xpu }} Target Descriptions -===//

#include "{{ Xpu }}MCTargetDesc.h"
#include "{{ Xpu }}AsmBackend.h"
// #include "{{ Xpu }}BaseInfo.h"
// #include "{{ Xpu }}ELFStreamer.h"
#include "{{ Xpu }}InstPrinter.h"
#include "{{ Xpu }}MCAsmInfo.h"
#include "TargetInfo/{{ Xpu }}TargetInfo.h"

#include "llvm/MC/MachineLocation.h"
#include "llvm/MC/MCAsmBackend.h"
#include "llvm/MC/MCAsmInfo.h"
#include "llvm/MC/MCCodeEmitter.h"
#include "llvm/MC/MCELFStreamer.h"
#include "llvm/MC/MCInstrAnalysis.h"
#include "llvm/MC/MCInstPrinter.h"
#include "llvm/MC/MCInstrInfo.h"
#include "llvm/MC/MCObjectFileInfo.h"
#include "llvm/MC/MCObjectWriter.h"
#include "llvm/MC/MCRegisterInfo.h"
#include "llvm/MC/MCSubtargetInfo.h"
#include "llvm/MC/MCSymbol.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/ErrorHandling.h"

using namespace llvm;

#define GET_INSTRINFO_MC_DESC
#define ENABLE_INSTR_PREDICATE_VERIFIER
#include "{{ Xpu }}GenInstrInfo.inc"

#define GET_SUBTARGETINFO_MC_DESC
#include "{{ Xpu }}GenSubtargetInfo.inc"

#define GET_REGINFO_MC_DESC
#include "{{ Xpu }}GenRegisterInfo.inc"

static MCInstrInfo *create{{ Xpu }}MCInstrInfo() {
  MCInstrInfo *X = new MCInstrInfo();
  Init{{ Xpu }}MCInstrInfo(X); // defined in {{ Xpu }}GenInstrInfo.inc
  return X;
}

static MCRegisterInfo *create{{ Xpu }}MCRegisterInfo(const Triple &TT) {
  MCRegisterInfo *X = new MCRegisterInfo();
  Init{{ Xpu }}MCRegisterInfo(X, {{ Xpu }}::{{ RA }}); // defined in {{ Xpu }}GenRegisterInfo.inc
  return X;
}

static MCSubtargetInfo *create{{ Xpu }}MCSubtargetInfo(const Triple &TT,
                                                      StringRef CPU, StringRef FS) {
  if (CPU.empty() || CPU == "generic") {
    if (TT.getArch() == llvm::Triple::{{ xpu }}64be)
      CPU = "xpu-64be";
    else if (TT.getArch() == llvm::Triple::{{ xpu }}64le)
      CPU = "xpu-64le";
    else if (TT.getArch() == llvm::Triple::{{ xpu }}32be)
      CPU = "xpu-32be";
    else if (TT.getArch() == llvm::Triple::{{ xpu }}32le)
      CPU = "xpu-32le";
  }
  return create{{ Xpu }}MCSubtargetInfoImpl(TT, CPU, /*TuneCPU*/CPU ,FS);
}

static MCAsmInfo *create{{ Xpu }}MCAsmInfo(const MCRegisterInfo &MRI,
                                           const Triple &TT,
                                           const MCTargetOptions &Options) {
  MCAsmInfo *MAI = new {{ Xpu }}MCAsmInfo(TT);
  unsigned SP = MRI.getDwarfRegNum({{ Xpu }}::{{ SP }}, true);
  MCCFIInstruction Inst = MCCFIInstruction::cfiDefCfa(nullptr, SP, 0);
  MAI->addInitialFrameState(Inst);
  return MAI;
}

static MCInstPrinter *create{{ Xpu }}MCInstPrinter(const Triple &T,
                                                   unsigned SyntaxVariant,
                                                   const MCAsmInfo &MAI,
                                                   const MCInstrInfo &MII,
                                                   const MCRegisterInfo &MRI) {
 return new {{ Xpu }}InstPrinter(MAI, MII, MRI);
}

namespace {

class {{ Xpu }}MCInstrAnalysis : public MCInstrAnalysis {
 public:
  {{ Xpu }}MCInstrAnalysis(const MCInstrInfo *Info) : MCInstrAnalysis(Info) {}
};
}

static MCInstrAnalysis *create{{ Xpu }}MCInstrAnalysis(const MCInstrInfo *Info) {
  return new {{ Xpu }}MCInstrAnalysis(Info);
}

extern "C" LLVM_EXTERNAL_VISIBILITY void LLVMInitialize{{ Xpu }}TargetMC() {
  for (Target *T : {&getThe{{ Xpu }}32leTarget(), &getThe{{ Xpu }}32beTarget(),
                    &getThe{{ Xpu }}64leTarget(), &getThe{{ Xpu }}64beTarget()}) {
    TargetRegistry::RegisterMCRegInfo(*T, create{{ Xpu }}MCRegisterInfo);
    TargetRegistry::RegisterMCInstrInfo(*T, create{{ Xpu }}MCInstrInfo);
    TargetRegistry::RegisterMCSubtargetInfo(*T, create{{ Xpu }}MCSubtargetInfo);
    TargetRegistry::RegisterMCAsmInfo(*T, create{{ Xpu }}MCAsmInfo);
    // TargetRegistry::RegisterMCInstrAnalysis(*T, create{{ Xpu }}MCInstrAnalysis);
    TargetRegistry::RegisterMCInstPrinter(*T, create{{ Xpu }}MCInstPrinter);
    TargetRegistry::RegisterMCCodeEmitter(*T, create{{ Xpu }}MCCodeEmitter);
    TargetRegistry::RegisterMCAsmBackend(*T, create{{ Xpu }}AsmBackend);
    // TargetRegistry::RegisterELFStreamer(*T, create{{ Xpu }}ELFStreamer);
    // TargetRegistry::RegisterObjectTargetStreamer(*T, create{{ Xpu }}ObjectTargetStreamer);
    // TargetRegistry::RegisterAsmTargetStreamer(*T, create{{ Xpu }}AsmTargetStreamer);
    // TargetRegistry::RegisterNullTargetStreamer(*T, create{{ Xpu }}NullTargetStreamer);
  }
}

