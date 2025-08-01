//===-- {{ Xpu }}InstrInfo.cpp - {{ Xpu }} Instruction Information -*- C++ -*-===//

#include "{{ Xpu }}InstrInfo.h"
#include "{{ Xpu }}.h"
// #include "{{ Xpu }}MachineFunctionInfo.h"
#include "llvm/CodeGen/MachineFrameInfo.h"
#include "{{ Xpu }}Subtarget.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/CodeGen/MachineBasicBlock.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/IR/DebugLoc.h"
#include "llvm/Support/ErrorHandling.h"
#include <cassert>
#include <iterator>

#define GET_INSTRINFO_CTOR_DTOR
#include "{{ Xpu }}GenInstrInfo.inc"

using namespace llvm;

{{ Xpu }}InstrInfo::{{ Xpu }}InstrInfo({{ Xpu }}Subtarget &STI)
    : {{ Xpu }}GenInstrInfo({{ Xpu }}::ADJCALLSTACKDOWN, {{ Xpu }}::ADJCALLSTACKUP),
      STI(STI) {}

// bool
// {{ Xpu }}InstrInfo::expandPostRAPseudo(MachineInstr &MI) const {
//   auto &MBB = *MI.getParent();
// 
//   switch(MI.getDesc().getOpcode()) {
//     default:
//       return false;
//     case {{ Xpu }}::PseudoXXX:
//       expandPseudoXXX(MBB, MI);
//       break;
//   }
// 
//   MBB.erase(MI);
//   return true;
// }

// void
// {{ Xpu }}InstrInfo::expandPseudoXXX(
//   MachineBasicBlock &MBB,
//   MachineBasicBlock::iterator I
// ) const {
//   // BuildMI(MBB, I, I->getDebugLoc(), get({{ Xpu }}::XXX))
//   //   .addReg({{ Xpu }}::X0).addReg({{ Xpu }}::X1).addImm(0);
// }

void
{{ Xpu }}InstrInfo::addImmediate(
  Register DstReg,
  Register SrcReg,
  int64_t Amount,
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI
) const {
  DebugLoc DL = MBBI != MBB.end() ? MBBI->getDebugLoc() : DebugLoc();
  MachineFunction *MF = MBB.getParent();
  MachineRegisterInfo &MRI = MF->getRegInfo();

  if (Amount == 0) {
    return;
  }
  {% for cond, vardefs, buildmis in addimm_codes -%}
  {{ cond }} {
  {%- for vardef in vardefs %}
    {{ vardef }}
  {%- endfor %}
  {%- for buildmi in buildmis %}
    {{ buildmi }}{%- endfor %}
  } {%- endfor %}
}

void
{{ Xpu }}InstrInfo::copyPhysReg(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  const DebugLoc &DL,
  MCRegister DstReg,
  MCRegister SrcReg,
  bool KillSrc,
  bool RenamableDest,
  bool RenamableSrc
) const {
  const TargetRegisterInfo *TRI = STI.getRegisterInfo();

  if ({{ Xpu }}::GPRRegClass.contains(DstReg, SrcReg)) {
    {{ copy_reg_buildmi }}
    return;
  }
}

void
{{ Xpu }}InstrInfo::storeRegToStackSlot(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator I,
  Register SrcReg, bool IsKill, int FI,
  const TargetRegisterClass *RC,
  const TargetRegisterInfo *TRI,
  Register VReg
) const {
  MachineFunction *MF = MBB.getParent();
  MachineFrameInfo &MFI = MF->getFrameInfo();

  unsigned Opcode = {{ Xpu }}::SW;
  MachineMemOperand *MMO = MF->getMachineMemOperand(
      MachinePointerInfo::getFixedStack(*MF, FI), MachineMemOperand::MOStore,
      MFI.getObjectSize(FI), MFI.getObjectAlign(FI));

  BuildMI(MBB, I, DebugLoc(), get(Opcode))
      .addReg(SrcReg, getKillRegState(IsKill))
      .addFrameIndex(FI)
      .addImm(0)
      .addMemOperand(MMO);
}

void
{{ Xpu }}InstrInfo::loadRegFromStackSlot(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator I,
  Register DstReg, int FI,
  const TargetRegisterClass *RC,
  const TargetRegisterInfo *TRI,
  Register VReg
) const {
  MachineFunction *MF = MBB.getParent();
  MachineFrameInfo &MFI = MF->getFrameInfo();

  unsigned Opcode = {{ Xpu }}::LW;
  MachineMemOperand *MMO = MF->getMachineMemOperand(
      MachinePointerInfo::getFixedStack(*MF, FI), MachineMemOperand::MOLoad,
      MFI.getObjectSize(FI), MFI.getObjectAlign(FI));

  BuildMI(MBB, I, DebugLoc(), get(Opcode), DstReg)
      .addFrameIndex(FI)
      .addImm(0)
      .addMemOperand(MMO);
}

unsigned
{{ Xpu }}InstrInfo::getInstSizeInBytes(
  const MachineInstr &MI
) const {
  if (MI.isMetaInstruction())
    return 0;

  switch (MI.getOpcode()) {
  default:
    return MI.getDesc().getSize();
  // case {{ Xpu }}::CONSTPOOL_ENTRY:
  //   return MI.getOperand(2).getImm();
  // case {{ Xpu }}::SPILL_CARRY:
  // case {{ Xpu }}::RESTORE_CARRY:
  // case {{ Xpu }}::PseudoTLSLA32:
  //   return 8;
  case TargetOpcode::INLINEASM_BR:
  case TargetOpcode::INLINEASM: {
    const MachineFunction *MF = MI.getParent()->getParent();
    const char *AsmStr = MI.getOperand(0).getSymbolName();
    return getInlineAsmLength(AsmStr, *MF->getTarget().getMCAsmInfo());
  }
  }
}

static void parseCondBranch(MachineInstr &LastInst, MachineBasicBlock *&Target,
                            SmallVectorImpl<MachineOperand> &Cond) {
  // Block ends with fall-through condbranch.
  assert(LastInst.getDesc().isConditionalBranch() &&
         "Unknown conditional branch");
  Target = LastInst.getOperand(2).getMBB();
  Cond.push_back(MachineOperand::CreateImm(LastInst.getOpcode()));
  Cond.push_back(LastInst.getOperand(0));
  Cond.push_back(LastInst.getOperand(1));
}

bool
{{ Xpu }}InstrInfo::analyzeBranch(
  MachineBasicBlock &MBB,
  MachineBasicBlock *&TBB,
  MachineBasicBlock *&FBB,
  SmallVectorImpl<MachineOperand> &Cond,
  bool AllowModify
) const {
  TBB = FBB = nullptr;
  Cond.clear();

  // If the block has no terminators, it just falls into the block after it.
  MachineBasicBlock::iterator I = MBB.getLastNonDebugInstr();
  if (I == MBB.end() || !isUnpredicatedTerminator(*I))
    return false;

  // Count the number of terminators and find the first unconditional or
  // indirect branch.
  MachineBasicBlock::iterator FirstUncondOrIndirectBr = MBB.end();
  int NumTerminators = 0;
  for (auto J = I.getReverse(); J != MBB.rend() && isUnpredicatedTerminator(*J);
       J++) {
    NumTerminators++;
    if (J->getDesc().isUnconditionalBranch() ||
        J->getDesc().isIndirectBranch()) {
      FirstUncondOrIndirectBr = J.getReverse();
    }
  }

  // If AllowModify is true, we can erase any terminators after
  // FirstUncondOrIndirectBR.
  if (AllowModify && FirstUncondOrIndirectBr != MBB.end()) {
    while (std::next(FirstUncondOrIndirectBr) != MBB.end()) {
      std::next(FirstUncondOrIndirectBr)->eraseFromParent();
      NumTerminators--;
    }
    I = FirstUncondOrIndirectBr;
  }

  // We can't handle blocks that end in an indirect branch.
  if (I->getDesc().isIndirectBranch())
    return true;

  // We can't handle Generic branch opcodes from Global ISel.
  if (I->isPreISelOpcode())
    return true;

  // We can't handle blocks with more than 2 terminators.
  if (NumTerminators > 2)
    return true;

  // Handle a single unconditional branch.
  if (NumTerminators == 1 && I->getDesc().isUnconditionalBranch()) {
    TBB = getBranchDestBlock(*I);
    return false;
  }

  // Handle a single conditional branch.
  if (NumTerminators == 1 && I->getDesc().isConditionalBranch()) {
    parseCondBranch(*I, TBB, Cond);
    return false;
  }

  // Handle a conditional branch followed by an unconditional branch.
  if (NumTerminators == 2 && std::prev(I)->getDesc().isConditionalBranch() &&
      I->getDesc().isUnconditionalBranch()) {
    parseCondBranch(*std::prev(I), TBB, Cond);
    FBB = getBranchDestBlock(*I);
    return false;
  }

  // Otherwise, we can't handle this.
  return true;
}

// Inserts a branch into the end of the specific MachineBasicBlock, returning
// the number of instructions inserted.
unsigned
{{ Xpu }}InstrInfo::insertBranch(
  MachineBasicBlock &MBB,
  MachineBasicBlock *TBB,
  MachineBasicBlock *FBB,
  ArrayRef<MachineOperand> Cond,
  const DebugLoc &DL,
  int *BytesAdded
) const {
  if (BytesAdded)
    *BytesAdded = 0;

  // Shouldn't be a fall through.
  assert(TBB && "insertBranch must not be told to insert a fallthrough");
  assert((Cond.size() == 3 || Cond.size() == 0) &&
         "{{ Xpu }} branch conditions have two components!");

  // Unconditional branch.
  if (Cond.empty()) {
    MachineInstr &MI = *BuildMI(&MBB, DL, get({{ Xpu }}::PseudoBR)).addMBB(TBB);
    if (BytesAdded)
      *BytesAdded += getInstSizeInBytes(MI);
    return 1;
  }

  // Either a one or two-way conditional branch.
  unsigned Opc = Cond[0].getImm();
  MachineInstr &CondMI = *BuildMI(&MBB, DL, get(Opc))
                                  .add(Cond[1])
                                  .add(Cond[2])
                                  .addMBB(TBB);
  if (BytesAdded)
    *BytesAdded += getInstSizeInBytes(CondMI);

  // One-way conditional branch.
  if (!FBB)
    return 1;

  // Two-way conditional branch.
  MachineInstr &MI = *BuildMI(&MBB, DL, get({{ Xpu }}::PseudoBR)).addMBB(FBB);
  if (BytesAdded)
    *BytesAdded += getInstSizeInBytes(MI);
  return 2;
}

unsigned
{{ Xpu }}InstrInfo::removeBranch(
  MachineBasicBlock &MBB,
  int *BytesRemoved
) const {
  if (BytesRemoved)
    *BytesRemoved = 0;
  MachineBasicBlock::iterator I = MBB.getLastNonDebugInstr();
  if (I == MBB.end())
    return 0;

  if (!I->getDesc().isUnconditionalBranch() &&
      !I->getDesc().isConditionalBranch())
    return 0;

  // Remove the branch.
  if (BytesRemoved)
    *BytesRemoved += getInstSizeInBytes(*I);
  I->eraseFromParent();

  I = MBB.end();

  if (I == MBB.begin())
    return 1;
  --I;
  if (!I->getDesc().isConditionalBranch())
    return 1;

  // Remove the branch.
  if (BytesRemoved)
    *BytesRemoved += getInstSizeInBytes(*I);
  I->eraseFromParent();
  return 2;
}

static unsigned getOppositeBranchOpc(unsigned Opcode) {
  switch (Opcode) {
  default:
    llvm_unreachable("Unknown conditional branch!");
  {%- for brop0, brop1 in opposite_br_codes %}
  case {{ brop0 }}: return {{ brop1 }};
  {%- endfor %}
  }
}

bool
{{ Xpu }}InstrInfo::reverseBranchCondition(
  SmallVectorImpl<MachineOperand> &Cond
) const {
  assert((Cond.size() == 3) && "Invalid branch condition!");
  Cond[0].setImm(getOppositeBranchOpc(Cond[0].getImm()));
  return false;
}

MachineBasicBlock *
{{ Xpu }}InstrInfo::getBranchDestBlock(const MachineInstr &MI) const {
  assert(MI.getDesc().isBranch() && "Unexpected opcode!");
  // The branch target is always the last operand.
  int NumOp = MI.getNumExplicitOperands();
  return MI.getOperand(NumOp - 1).getMBB();
}
