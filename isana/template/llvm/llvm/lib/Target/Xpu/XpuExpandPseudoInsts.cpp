//===-- {{ Xpu }}ExpandPseudoInsts.cpp - Expand pseudo instructions -*- C++ -*-===//

#include "{{ Xpu }}.h"
#include "{{ Xpu }}InstrInfo.h"
#include "{{ Xpu }}TargetMachine.h"

#include "llvm/CodeGen/LivePhysRegs.h"
#include "llvm/CodeGen/MachineFunctionPass.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/MC/MCContext.h"

using namespace llvm;

#define {{ XPU }}_PRERA_EXPAND_PSEUDO_NAME "{{ Xpu }} Pre-RA pseudo instruction expansion pass"
#define {{ XPU }}_POSTRA_EXPAND_PSEUDO_NAME "{{ Xpu }} Post-RA pseudo instruction expansion pass"
#define {{ XPU }}_EXPAND_PSEUDO_NAME "{{ Xpu }} pseudo instruction expansion pass"

namespace {

class {{ Xpu }}PreRAExpandPseudo : public MachineFunctionPass {
public:
  const {{ Xpu }}Subtarget *STI;
  const {{ Xpu }}InstrInfo *TII;
  static char ID;

  {{ Xpu }}PreRAExpandPseudo() : MachineFunctionPass(ID) {}

  bool runOnMachineFunction(MachineFunction &MF) override;

  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.setPreservesCFG();
    MachineFunctionPass::getAnalysisUsage(AU);
  }
  StringRef getPassName() const override { return {{ XPU }}_PRERA_EXPAND_PSEUDO_NAME; }

private:
  bool expandMBB(MachineBasicBlock &MBB);
  bool expandMI(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI,
                MachineBasicBlock::iterator &NextMBBI);
  {% for pseudo in pseudo_instrs %}
  bool expand{{ pseudo.name }}(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI, MachineBasicBlock::iterator &NextMBBI);
  {%- endfor %}

#ifndef NDEBUG
  unsigned getInstSizeInBytes(const MachineFunction &MF) const {
    unsigned Size = 0;
    for (auto &MBB : MF)
      for (auto &MI : MBB)
        Size += TII->getInstSizeInBytes(MI);
    return Size;
  }
#endif
};

char {{ Xpu }}PreRAExpandPseudo::ID = 0;

bool {{ Xpu }}PreRAExpandPseudo::runOnMachineFunction(MachineFunction &MF) {
  STI = &MF.getSubtarget<{{ Xpu }}Subtarget>();
  TII = STI->getInstrInfo();

#ifndef NDEBUG
  const unsigned OldSize = getInstSizeInBytes(MF);
#endif

  bool Modified = false;
  for (auto &MBB : MF)
    Modified |= expandMBB(MBB);

#ifndef NDEBUG
  const unsigned NewSize = getInstSizeInBytes(MF);
  assert(OldSize >= NewSize);
#endif
  return Modified;
}

bool {{ Xpu }}PreRAExpandPseudo::expandMBB(MachineBasicBlock &MBB) {
  bool Modified = false;

  MachineBasicBlock::iterator MBBI = MBB.begin(), E = MBB.end();
  while (MBBI != E) {
    MachineBasicBlock::iterator NMBBI = std::next(MBBI);
    Modified |= expandMI(MBB, MBBI, NMBBI);
    MBBI = NMBBI;
  }

  return Modified;
}

bool {{ Xpu }}PreRAExpandPseudo::expandMI(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  MachineBasicBlock::iterator &NextMBBI
) {
  switch (MBBI->getOpcode()) {
  default:
    break;
  {% for pseudo in pseudo_pre_ra_instrs %}
  case {{ Xpu }}::Pseudo{{ pseudo.name }}:
    return expand{{ pseudo.name }}(MBB, MBBI, NextMBBI);
  {%- endfor %}
  }
  return false;
}

{% for pseudo in pseudo_pre_ra_instrs %}
bool {{ Xpu }}ExpandPseudo::expand{{ pseudo.name }}(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  MachineBasicBlock::iterator &NextMBBI
) {
  MachineFunction *MF = MBB.getParent();
  MachineInstr &MI = *MBBI;
  DebugLoc DL = MI.getDebugLoc();

  {% for line in pseudo.buildmi %}
  {{ line }}
  {%- endfor %}

  MBBI->eraseFromParent();
  return true;
}
{% endfor %}

class {{ Xpu }}PostRAExpandPseudo : public MachineFunctionPass {
public:
  const {{ Xpu }}Subtarget *STI;
  const {{ Xpu }}InstrInfo *TII;
  static char ID;

  {{ Xpu }}PostRAExpandPseudo() : MachineFunctionPass(ID) {}

  bool runOnMachineFunction(MachineFunction &MF) override;

  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.setPreservesCFG();
    MachineFunctionPass::getAnalysisUsage(AU);
  }
  StringRef getPassName() const override { return {{ XPU }}_POSTRA_EXPAND_PSEUDO_NAME; }

private:
  bool expandMBB(MachineBasicBlock &MBB);
  bool expandMI(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI,
                MachineBasicBlock::iterator &NextMBBI);
  {% for pseudo in pseudo_instrs %}
  bool expand{{ pseudo.name }}(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI, MachineBasicBlock::iterator &NextMBBI);
  {%- endfor %}

#ifndef NDEBUG
  unsigned getInstSizeInBytes(const MachineFunction &MF) const {
    unsigned Size = 0;
    for (auto &MBB : MF)
      for (auto &MI : MBB)
        Size += TII->getInstSizeInBytes(MI);
    return Size;
  }
#endif
};

char {{ Xpu }}PostRAExpandPseudo::ID = 0;

bool {{ Xpu }}PostRAExpandPseudo::runOnMachineFunction(MachineFunction &MF) {
  STI = &MF.getSubtarget<{{ Xpu }}Subtarget>();
  TII = STI->getInstrInfo();

#ifndef NDEBUG
  const unsigned OldSize = getInstSizeInBytes(MF);
#endif

  bool Modified = false;
  for (auto &MBB : MF)
    Modified |= expandMBB(MBB);

#ifndef NDEBUG
  const unsigned NewSize = getInstSizeInBytes(MF);
  assert(OldSize >= NewSize);
#endif
  return Modified;
}

bool {{ Xpu }}PostRAExpandPseudo::expandMBB(MachineBasicBlock &MBB) {
  bool Modified = false;

  MachineBasicBlock::iterator MBBI = MBB.begin(), E = MBB.end();
  while (MBBI != E) {
    MachineBasicBlock::iterator NMBBI = std::next(MBBI);
    Modified |= expandMI(MBB, MBBI, NMBBI);
    MBBI = NMBBI;
  }

  return Modified;
}

bool {{ Xpu }}PostRAExpandPseudo::expandMI(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  MachineBasicBlock::iterator &NextMBBI
) {
  switch (MBBI->getOpcode()) {
  default:
    break;
  {% for pseudo in pseudo_post_ra_instrs %}
  case {{ Xpu }}::Pseudo{{ pseudo.name }}:
    return expand{{ pseudo.name }}(MBB, MBBI, NextMBBI);
  {%- endfor %}
  }
  return false;
}

{% for pseudo in pseudo_post_ra_instrs %}
bool {{ Xpu }}ExpandPseudo::expand{{ pseudo.name }}(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  MachineBasicBlock::iterator &NextMBBI
) {
  MachineFunction *MF = MBB.getParent();
  MachineInstr &MI = *MBBI;
  DebugLoc DL = MI.getDebugLoc();

  {% for line in pseudo.buildmi %}
  {{ line }}
  {%- endfor %}

  MBBI->eraseFromParent();
  return true;
}
{% endfor %}

class {{ Xpu }}ExpandPseudo : public MachineFunctionPass {
public:
  const {{ Xpu }}Subtarget *STI;
  const {{ Xpu }}InstrInfo *TII;
  static char ID;

  {{ Xpu }}ExpandPseudo() : MachineFunctionPass(ID) {}

  bool runOnMachineFunction(MachineFunction &MF) override;

  StringRef getPassName() const override { return {{ XPU }}_EXPAND_PSEUDO_NAME; }

private:
  bool expandMBB(MachineBasicBlock &MBB);
  bool expandMI(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI,
                MachineBasicBlock::iterator &NextMBBI);
  {% for pseudo in pseudo_instrs %}
  bool expand{{ pseudo.name }}(MachineBasicBlock &MBB, MachineBasicBlock::iterator MBBI, MachineBasicBlock::iterator &NextMBBI);
  {%- endfor %}
#ifndef NDEBUG
  unsigned getInstSizeInBytes(const MachineFunction &MF) const {
    unsigned Size = 0;
    for (auto &MBB : MF)
      for (auto &MI : MBB)
        Size += TII->getInstSizeInBytes(MI);
    return Size;
  }
#endif
};

char {{ Xpu }}ExpandPseudo::ID = 0;

bool {{ Xpu }}ExpandPseudo::runOnMachineFunction(MachineFunction &MF) {
  STI = &MF.getSubtarget<{{ Xpu }}Subtarget>();
  TII = STI->getInstrInfo();

#ifndef NDEBUG
  const unsigned OldSize = getInstSizeInBytes(MF);
#endif

  bool Modified = false;
  for (auto &MBB : MF)
    Modified |= expandMBB(MBB);

#ifndef NDEBUG
  const unsigned NewSize = getInstSizeInBytes(MF);
  assert(OldSize >= NewSize);
#endif
  return Modified;
}

bool {{ Xpu }}ExpandPseudo::expandMBB(MachineBasicBlock &MBB) {
  bool Modified = false;

  MachineBasicBlock::iterator MBBI = MBB.begin(), E = MBB.end();
  while (MBBI != E) {
    MachineBasicBlock::iterator NMBBI = std::next(MBBI);
    Modified |= expandMI(MBB, MBBI, NMBBI);
    MBBI = NMBBI;
  }

  return Modified;
}

bool {{ Xpu }}ExpandPseudo::expandMI(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  MachineBasicBlock::iterator &NextMBBI
) {
  switch (MBBI->getOpcode()) {
  default:
    break;
  {% for pseudo in pseudo_instrs %}
  case {{ Xpu }}::Pseudo{{ pseudo.name }}:
    return expand{{ pseudo.name }}(MBB, MBBI, NextMBBI);
  {%- endfor %}
  }

  return false;
}

{% for pseudo in pseudo_instrs %}
bool {{ Xpu }}ExpandPseudo::expand{{ pseudo.name }}(
  MachineBasicBlock &MBB,
  MachineBasicBlock::iterator MBBI,
  MachineBasicBlock::iterator &NextMBBI
) {
  // MachineFunction *MF = MBB.getParent();
  MachineInstr &MI = *MBBI;
  DebugLoc DL = MI.getDebugLoc();
{% for line in pseudo.buildmi %}
  {{ line }}
{%- endfor %}

  MBBI->eraseFromParent();
  return true;
}
{% endfor %}

} // end of anonymous namespace

INITIALIZE_PASS({{ Xpu }}PreRAExpandPseudo, "{{ xpu }}-prera-expand-pseudo",
    {{ XPU }}_PRERA_EXPAND_PSEUDO_NAME, false, false)

INITIALIZE_PASS({{ Xpu }}PostRAExpandPseudo, "{{ xpu }}-postra-expand-pseudo",
    {{ XPU }}_POSTRA_EXPAND_PSEUDO_NAME, false, false)

INITIALIZE_PASS({{ Xpu }}ExpandPseudo, "{{ xpu }}-expand-pseudo",
    {{ XPU }}_EXPAND_PSEUDO_NAME, false, false)

namespace llvm {

FunctionPass *create{{ Xpu }}PreRAExpandPseudoPass() { return new {{ Xpu }}PreRAExpandPseudo(); }
FunctionPass *create{{ Xpu }}PostRAExpandPseudoPass() { return new {{ Xpu }}PostRAExpandPseudo(); }
FunctionPass *create{{ Xpu }}ExpandPseudoPass() { return new {{ Xpu }}ExpandPseudo(); }

} // end of namespace llvm
