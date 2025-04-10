//===-- {{ Xpu }}FrameLowering.cpp - {{ Xpu }} Frame Information -*- C++ -*-===//

#include "{{ Xpu }}FrameLowering.h"
#include "{{ Xpu }}InstrInfo.h"
#include "{{ Xpu }}Subtarget.h"
#include "llvm/CodeGen/MachineFrameInfo.h"
#include "llvm/CodeGen/MachineFunction.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/CodeGen/MachineRegisterInfo.h"

using namespace llvm;

bool {{ Xpu }}FrameLowering::hasFP(
  const MachineFunction &MF
) const {
  const TargetRegisterInfo *RegInfo = MF.getSubtarget().getRegisterInfo();

  const MachineFrameInfo &MFI = MF.getFrameInfo();
  return MF.getTarget().Options.DisableFramePointerElim(MF) ||
         RegInfo->hasStackRealignment(MF) || MFI.hasVarSizedObjects() ||
         MFI.isFrameAddressTaken();
}

void {{ Xpu }}FrameLowering::emitPrologue(
  MachineFunction &MF,
  MachineBasicBlock &MBB
) const {
  MachineFrameInfo &MFI = MF.getFrameInfo();
  MachineBasicBlock::iterator MBBI = MBB.begin();
  const auto &TII = *static_cast<const {{ Xpu }}InstrInfo *>(STI.getInstrInfo());

  // Debug location must be unknown since the first debug location is used
  // to determine the end of the prologue.
  DebugLoc DL;

  uint64_t StackSize = MFI.getStackSize();

  if (StackSize == 0 && !MFI.adjustsStack())
    return;

  Register DstReg = {{ Xpu }}::{{ SP }};
  Register SrcReg = {{ Xpu }}::{{ SP }};
  TII.addImmediate(DstReg, SrcReg, -StackSize, MBB, MBBI);
}

void {{ Xpu }}FrameLowering::emitEpilogue(
  MachineFunction &MF,
  MachineBasicBlock &MBB
) const {
  MachineFrameInfo &MFI = MF.getFrameInfo();
  MachineBasicBlock::iterator MBBI = MBB.getLastNonDebugInstr();
  const auto &TII = *static_cast<const {{ Xpu }}InstrInfo *>(STI.getInstrInfo());

  DebugLoc DL;

  uint64_t StackSize = MFI.getStackSize();

  if (StackSize == 0)
    return;

  Register DstReg = {{ Xpu }}::{{ SP }};
  Register SrcReg = {{ Xpu }}::{{ SP }};
  TII.addImmediate(DstReg, SrcReg, StackSize, MBB, MBBI);
}

void {{ Xpu }}FrameLowering::determineCalleeSaves(
  MachineFunction &MF,
  BitVector &SavedRegs,
  RegScavenger *RS
) const {
  TargetFrameLowering::determineCalleeSaves(MF, SavedRegs, RS);

  if (hasFP(MF)) {
    SavedRegs.set({{ Xpu }}::{{ RA }});
  }
}

MachineBasicBlock::iterator
{{ Xpu }}FrameLowering::eliminateCallFramePseudoInstr(
  MachineFunction &MF, MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI
) const {
  const auto &TII = *static_cast<const {{ Xpu }}InstrInfo *>(STI.getInstrInfo());

  if (!hasReservedCallFrame(MF)) {
    int64_t Amount = MBBI->getOperand(0).getImm();

    if (MBBI->getOpcode() == {{ Xpu }}::ADJCALLSTACKDOWN)
      Amount = -Amount;

    Register DstReg = {{ Xpu }}::{{ SP }};
    Register SrcReg = {{ Xpu }}::{{ SP }};
    TII.addImmediate(DstReg, SrcReg, Amount, MBB, MBBI);
  }

  return MBB.erase(MBBI);
}
