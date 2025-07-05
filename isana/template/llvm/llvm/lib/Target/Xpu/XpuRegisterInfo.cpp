//===-- {{ Xpu }}RegisterInfo.cpp - {{ Xpu }} Register Information -*- C++ -*-===//

#include "{{ Xpu }}RegisterInfo.h"
#include "{{ Xpu }}.h"
#include "{{ Xpu }}Subtarget.h"
#include "llvm/CodeGen/MachineFrameInfo.h"
#include "llvm/CodeGen/MachineFunction.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/CodeGen/RegisterScavenging.h"
#include "llvm/CodeGen/TargetFrameLowering.h"
#include "llvm/CodeGen/TargetInstrInfo.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/ErrorHandling.h"

using namespace llvm;

#define DEBUG_TYPE "{{ xpu }}-reg-info"

#define GET_REGINFO_TARGET_DESC
#include "{{ Xpu }}GenRegisterInfo.inc"

{{ Xpu }}RegisterInfo::{{ Xpu }}RegisterInfo()
    : {{ Xpu }}GenRegisterInfo({{ Xpu }}::{{ REG0 }}) {}

const MCPhysReg *
{{ Xpu }}RegisterInfo::getCalleeSavedRegs(const MachineFunction *MF) const {
  return CSR_ABI0_SaveList;
}

const uint32_t *
{{ Xpu }}RegisterInfo::getCallPreservedMask(const MachineFunction &MF,
                                            CallingConv::ID CC) const {
  return CSR_ABI0_RegMask;
}

BitVector
{{ Xpu }}RegisterInfo::getReservedRegs(const MachineFunction &MF) const {
  BitVector Reserved(getNumRegs());
  {% for reg in reserved_regs -%}
  markSuperRegs(Reserved, {{ Xpu }}::{{ reg }});
  {% endfor -%}
  return Reserved;
}

bool
{{ Xpu }}RegisterInfo::eliminateFrameIndex(MachineBasicBlock::iterator MBBI,
                                           int SPAdj, unsigned FIOperandNum,
                                           RegScavenger *RS) const {
  MachineInstr &MI = *MBBI;
  MachineBasicBlock &MBB = *MI.getParent();
  MachineFunction &MF = *MBB.getParent();
  const TargetInstrInfo *TII = MF.getSubtarget().getInstrInfo();
  DebugLoc DL;
  if (MBBI != MBB.end())
    DL = MBBI->getDebugLoc();

  unsigned i = 0;
  while (!MI.getOperand(i).isFI()) {
    ++i;
    assert(i < MI.getNumOperands() && "Instr doesn't have FrameIndex operand!");
  }

  Register FrameReg = {{ Xpu }}::{{ SP }};
  int FrameIndex = MI.getOperand(FIOperandNum).getIndex();
  uint64_t StackSize = MF.getFrameInfo().getStackSize();
  int64_t SpOffset = MF.getFrameInfo().getObjectOffset(FrameIndex);

  int64_t OldOffset = MI.getOperand(i+1).getImm();

  int64_t NewOffset = SpOffset + (int64_t)StackSize;
  NewOffset += OldOffset;

  // before:
  //   PseudoFI_ld/st val, fiaddr, fioff
  // aftter (small offset):
  //   ld/st val, sp, fioff+spoff
  // aftter (large offset):
  //   lui  t0, fioff_hi+spoff_hi
  //   add  dstaddr, sp, t0
  //   ld/st val, dstaddr, fioff_lo+spoff_lo

  int64_t NewLo12 = SignExtend64<12>(NewOffset);
  int64_t NewHi20 = ((NewOffset - NewLo12) >> 12);

  MI.getOperand(i+0).ChangeToRegister(FrameReg, false);
  MI.getOperand(i+1).ChangeToImmediate(NewLo12);

  if (NewHi20) {
    MachineRegisterInfo &MRI = MBB.getParent()->getRegInfo();
    Register TempReg = MRI.createVirtualRegister(&{{ Xpu }}::GPRRegClass);
    BuildMI(MBB, MBBI, DL, TII->get({{ Xpu }}::LUI), TempReg)
      .addImm(NewHi20);
    BuildMI(MBB, MBBI, DL, TII->get({{ Xpu }}::ADD), TempReg)
      .addReg(FrameReg)
      .addReg(TempReg);
    MI.getOperand(i+0).ChangeToRegister(TempReg, false);
  }

  DenseMap<unsigned, unsigned> LoadMap;
  {%- for line in frameindex_load_maps %}
  {{ line }}
  {%- endfor %}
  DenseMap<unsigned, unsigned> StoreMap;
  {%- for line in frameindex_store_maps %}
  {{ line }}
  {%- endfor %}

  if (MI.getOpcode() == {{ Xpu }}::PseudoFI_LA) {
    BuildMI(MBB, MBBI, DL, TII->get({{ Xpu }}::ADDI), MI.getOperand(0).getReg())
      .addReg(MI.getOperand(1).getReg())
      .addImm(MI.getOperand(2).getImm());
    MI.eraseFromParent();
  } else if (LoadMap.contains(MI.getOpcode())) {
    {%- for line in frameindex_load_buildmi %}
    {{ line }}
    {%- endfor %}
    MI.eraseFromParent();
  } else if (StoreMap.contains(MI.getOpcode())) {
    {%- for line in frameindex_store_buildmi %}
    {{ line }}
    {%- endfor %}
    MI.eraseFromParent();
  }

  return false;
}

Register
{{ Xpu }}RegisterInfo::getFrameRegister(const MachineFunction &MF) const {
  const TargetFrameLowering *TFI = getFrameLowering(MF);
  return TFI->hasFP(MF) ? {{ Xpu }}::{{ FP }} : {{ Xpu }}::{{ SP }};
}
