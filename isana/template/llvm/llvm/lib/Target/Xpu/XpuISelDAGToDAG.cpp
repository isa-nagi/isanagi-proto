//===-- {{ Xpu }}ISelDAGToDAG.cpp - A Dag to Dag Inst Selector for {{ Xpu }} -*- C++ -*-===//

#include "{{ Xpu }}ISelDAGToDAG.h"
// #include "MCTargetDesc/{{ Xpu }}BaseInfo.h"
#include "{{ Xpu }}.h"
// #include "{{ Xpu }}MachineFunction.h"
#include "{{ Xpu }}RegisterInfo.h"
#include "llvm/CodeGen/MachineConstantPool.h"
#include "llvm/CodeGen/MachineFrameInfo.h"
#include "llvm/CodeGen/MachineFunction.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/CodeGen/MachineRegisterInfo.h"
#include "llvm/CodeGen/SelectionDAG.h"
#include "llvm/CodeGen/SelectionDAGNodes.h"
#include "llvm/CodeGen/StackProtector.h"
#include "llvm/IR/CFG.h"
#include "llvm/IR/GlobalValue.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Intrinsics.h"
#include "llvm/IR/Type.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/ErrorHandling.h"
#include "llvm/Support/KnownBits.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Target/TargetMachine.h"
using namespace llvm;

#define DEBUG_TYPE "{{ xpu }}-isel"
#define PASS_NAME "{{ Xpu }} DAG->DAG Pattern Instruction Selection"

//===----------------------------------------------------------------------===//
// Instruction Selector Implementation
//===----------------------------------------------------------------------===//

//===----------------------------------------------------------------------===//
// {{ Xpu }}DAGToDAGISel - {{ Xpu }} specific code to select {{ Xpu }} machine
// instructions for SelectionDAG operations.
//===----------------------------------------------------------------------===//

bool {{ Xpu }}DAGToDAGISel::runOnMachineFunction(MachineFunction &MF) {
  Subtarget = &MF.getSubtarget<{{ Xpu }}Subtarget>();
  bool Ret = SelectionDAGISel::runOnMachineFunction(MF);

  // processFunctionAfterISel(MF);

  return Ret;
}

bool {{ Xpu }}DAGToDAGISel::SelectAddrFrameIndexRegImm(
  SDValue Addr,
  SDValue &Base,
  SDValue &Offset
) {
  auto VT = MVT::i32;
  SDLoc DL(Addr);

  // (frameindex) -> (frameindex, 0)
  if (auto *FIN = dyn_cast<FrameIndexSDNode>(Addr)) {
    Base = CurDAG->getTargetFrameIndex(FIN->getIndex(), VT);
    Offset = CurDAG->getTargetConstant(0, DL, VT);
    return true;
  }

  if (CurDAG->isBaseWithConstantOffset(Addr)) {
    // (add frameindex, imm) -> (frameindex, imm)
    if (auto *FIN = dyn_cast<FrameIndexSDNode>(Addr.getOperand(0))) {
      int64_t CVal = cast<ConstantSDNode>(Addr.getOperand(1))->getSExtValue();
      Base = CurDAG->getTargetFrameIndex(FIN->getIndex(), VT);
      Offset = CurDAG->getSignedConstant(CVal, DL, VT, /*isTarget=*/true);
      return true;
    }
  }

  return false;
}

bool {{ Xpu }}DAGToDAGISel::SelectAddrRegImm(
  SDValue Addr,
  SDValue &Base,
  SDValue &Offset
) {
  auto VT = MVT::i32;
  SDLoc DL(Addr);

  if (SelectAddrFrameIndexRegImm(Addr, Base, Offset)) {
    return false;
  }

  if (CurDAG->isBaseWithConstantOffset(Addr)) {
    // (add addr, imm) -> (addr, imm)
    int64_t CVal = cast<ConstantSDNode>(Addr.getOperand(1))->getSExtValue();
    if (isInt<12>(CVal)) {
      Base = Addr.getOperand(0);
      Offset = CurDAG->getTargetConstant(CVal, DL, VT);
    } else {
      int64_t Lo = SignExtend64<12>(CVal);
      int64_t Hi = ((uint64_t)CVal - (uint64_t)Lo) >> 12;
      auto Lui = SDValue(CurDAG->getMachineNode({{ Xpu }}::LUI, DL, VT,
                                                CurDAG->getTargetConstant(Hi, DL, VT)), 0);
      Base = SDValue(CurDAG->getMachineNode({{ Xpu }}::ADD, DL, VT, Addr.getOperand(0), Lui), 0);
      Offset = CurDAG->getTargetConstant(Lo, DL, VT);
    }
    return true;
  }

    // (imm) -> (zero, imm)
  if (auto *C = dyn_cast<ConstantSDNode>(Addr)) {
    int64_t CVal = C->getZExtValue();
    if (isInt<12>(CVal)) {
      Base = CurDAG->getRegister({{ Xpu }}::X0, VT);
      // Offset = Addr;
      Offset = CurDAG->getTargetConstant(CVal, DL, VT);
    } else {
      int64_t Lo = SignExtend64<12>(CVal);
      int64_t Hi = ((uint64_t)CVal - (uint64_t)Lo) >> 12;
      Base = SDValue(CurDAG->getMachineNode({{ Xpu }}::LUI, DL, VT,
                                            CurDAG->getTargetConstant(Hi, DL, VT)), 0);
      Offset = CurDAG->getTargetConstant(Lo, DL, VT);
    }
    return true;
  }

  Base = Addr;
  Offset = CurDAG->getTargetConstant(0, DL, VT);
  return true;
}

/// Select instructions not customized! Used for
/// expanded, promoted and normal instructions
void {{ Xpu }}DAGToDAGISel::Select(SDNode *Node) {
  // unsigned Opcode = Node->getOpcode();

  // If we have a custom node, we already have selected!
  if (Node->isMachineOpcode()) {
    LLVM_DEBUG(errs() << "== "; Node->dump(CurDAG); errs() << "\n");
    Node->setNodeId(-1);
    return;
  }

  // See if subclasses can handle this node.
  // if (trySelect(Node))
  //   return;

  // Select the default instruction
  SelectCode(Node);
}

bool {{ Xpu }}DAGToDAGISel::SelectInlineAsmMemoryOperand(
    const SDValue &Op, InlineAsm::ConstraintCode ConstraintID,
    std::vector<SDValue> &OutOps) {
  // All memory constraints can at least accept raw pointers.
  switch(ConstraintID) {
  default:
    llvm_unreachable("Unexpected asm memory constraint");
  case InlineAsm::ConstraintCode::m:
  case InlineAsm::ConstraintCode::R:
  case InlineAsm::ConstraintCode::ZC:
    OutOps.push_back(Op);
    return false;
  }
  return true;
}

char {{ Xpu }}DAGToDAGISelLegacy::ID = 0;

{{ Xpu }}DAGToDAGISelLegacy::{{ Xpu }}DAGToDAGISelLegacy(
    {{ Xpu }}TargetMachine &TM, CodeGenOptLevel OptLevel)
      : SelectionDAGISelLegacy(
            ID, std::make_unique<{{ Xpu }}DAGToDAGISel>(TM, OptLevel)) {}

INITIALIZE_PASS({{ Xpu }}DAGToDAGISelLegacy, DEBUG_TYPE, PASS_NAME, false, false)

FunctionPass *llvm::create{{ Xpu }}ISelDag({{ Xpu }}TargetMachine &TM,
                                           CodeGenOptLevel OptLevel) {
  return new {{ Xpu }}DAGToDAGISelLegacy(TM, OptLevel);
}
