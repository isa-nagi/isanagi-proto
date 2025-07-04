//===-- {{ Xpu }}InstrInfo.h - {{ Xpu }} Instruction Information -*- C++ -*-===//

#ifndef LLVM_LIB_TARGET_{{ XPU }}_{{ XPU }}INSTRINFO_H
#define LLVM_LIB_TARGET_{{ XPU }}_{{ XPU }}INSTRINFO_H

#include "{{ Xpu }}RegisterInfo.h"
#include "llvm/CodeGen/TargetInstrInfo.h"

#define GET_INSTRINFO_HEADER
#include "{{ Xpu }}GenInstrInfo.inc"

namespace llvm {

class {{ Xpu }}Subtarget;

class {{ Xpu }}InstrInfo : public {{ Xpu }}GenInstrInfo {
public:
  {{ Xpu }}InstrInfo({{ Xpu }}Subtarget &STI);

  // bool expandPostRAPseudo(MachineInstr &MI) const override;

  void addImmediate(Register DstReg, Register SrcReg, int64_t Amount,
                    MachineBasicBlock &MBB,
                    MachineBasicBlock::iterator I) const;

  void copyPhysReg(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI,
                   const DebugLoc &DL, MCRegister DstReg, MCRegister SrcReg,
                   bool KillSrc, bool RenamableDest = false,
                   bool RenamableSrc = false) const override;

  void storeRegToStackSlot(MachineBasicBlock &MBB,
                           MachineBasicBlock::iterator MBBI, Register SrcReg,
                           bool IsKill, int FrameIndex,
                           const TargetRegisterClass *RC,
                           const TargetRegisterInfo *TRI,
                           Register VReg) const override;

  void loadRegFromStackSlot(MachineBasicBlock &MBB,
                            MachineBasicBlock::iterator MBBI, Register DstReg,
                            int FrameIndex, const TargetRegisterClass *RC,
                            const TargetRegisterInfo *TRI,
                            Register VReg) const override;

  unsigned getInstSizeInBytes(const MachineInstr &MI) const override;

  bool analyzeBranch(MachineBasicBlock &MBB, MachineBasicBlock *&TBB,
                     MachineBasicBlock *&FBB,
                     SmallVectorImpl<MachineOperand> &Cond,
                     bool AllowModify) const override;

  unsigned insertBranch(MachineBasicBlock &MBB, MachineBasicBlock *TBB,
                        MachineBasicBlock *FBB, ArrayRef<MachineOperand> Cond,
                        const DebugLoc &dl,
                        int *BytesAdded = nullptr) const override;

  unsigned removeBranch(MachineBasicBlock &MBB,
                        int *BytesRemoved = nullptr) const override;

  bool
  reverseBranchCondition(SmallVectorImpl<MachineOperand> &Cond) const override;

  MachineBasicBlock *getBranchDestBlock(const MachineInstr &MI) const override;

protected:
  const {{ Xpu }}Subtarget &STI;

private:
  // void expandPseudoXXX(MachineBasicBlock &MBB, MachineBasicBlock::iterator I) const;
};
}

#endif
