//===-- {{ Xpu }}ISelLowering.cpp - {{ Xpu }} DAG Lowering Implementation -*- C++ -*-===//

#include "{{ Xpu }}ISelLowering.h"
#include "{{ Xpu }}.h"
#include "{{ Xpu }}MachineFunctionInfo.h"
#include "{{ Xpu }}Subtarget.h"
#include "{{ Xpu }}TargetMachine.h"
#include "MCTargetDesc/{{ Xpu }}BaseInfo.h"
#include "llvm/CodeGen/CallingConvLower.h"
#include "llvm/CodeGen/MachineFrameInfo.h"
#include "llvm/CodeGen/MachineFunction.h"
#include "llvm/CodeGen/MachineInstrBuilder.h"
#include "llvm/CodeGen/MachineRegisterInfo.h"
#include "llvm/CodeGen/TargetLoweringObjectFileImpl.h"
#include "llvm/CodeGen/ValueTypes.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/ErrorHandling.h"
#include "llvm/Support/MathExtras.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

#define DEBUG_TYPE "{{ xpu }}-lower"

{{ Xpu }}TargetLowering::{{ Xpu }}TargetLowering(const TargetMachine &TM,
                                                 const {{ Xpu }}Subtarget &STI)
    : TargetLowering(TM), Subtarget(STI) {

  MVT XLenVT = Subtarget.getXLenVT();

  // Set up the register classes.
  addRegisterClass(MVT::i32, &{{ Xpu }}::GPRRegClass);

  // Compute derived properties from the register classes
  computeRegisterProperties(Subtarget.getRegisterInfo());

  setOperationAction({ISD::SMUL_LOHI, ISD::UMUL_LOHI}, XLenVT, Expand);
  setOperationAction(ISD::BSWAP, XLenVT, Expand);  // TODO: Zbb | Zbkb => Legal
  setOperationAction({ISD::CTTZ, ISD::CTLZ, ISD::CTPOP}, XLenVT, Expand);
  setOperationAction({ISD::ROTL, ISD::ROTR}, XLenVT, Expand);  // TODO: Zbb | Zbkb => Legal
                                                               //
  setOperationAction(ISD::SIGN_EXTEND_INREG, MVT::i1, Expand);
  setOperationAction(ISD::SIGN_EXTEND_INREG, {MVT::i8, MVT::i16}, Expand);  // TODO: zbb => delete this

  setOperationAction(ISD::BR_JT, MVT::Other, Expand);
  setOperationAction(ISD::BR_CC, XLenVT, Expand);
  // setOperationAction(ISD::BRCOND, MVT::Other, Custom);
  setOperationAction(ISD::SELECT   , XLenVT, Custom);
  setOperationAction(ISD::SELECT_CC, XLenVT, Expand);

  setOperationAction(ISD::VASTART,   MVT::Other, Custom);
  setOperationAction(ISD::VAARG,     MVT::Other, Expand);
  setOperationAction(ISD::VACOPY,    MVT::Other, Expand);
  setOperationAction(ISD::VAEND,     MVT::Other, Expand);

  setOperationAction(ISD::GlobalAddress, XLenVT, Custom);
  setOperationAction(ISD::ConstantPool, XLenVT, Custom);

  // Function alignments
  setMinFunctionAlignment(Align(4));
  setPrefFunctionAlignment(Align(4));
}

// addLiveIn - This helper function adds the specified physical register to the
// MachineFunction as a live in value.  It also creates a corresponding
// virtual register for it.
static unsigned
addLiveIn(MachineFunction &MF, unsigned PReg, const TargetRegisterClass *RC)
{
  Register VReg = MF.getRegInfo().createVirtualRegister(RC);
  MF.getRegInfo().addLiveIn(PReg, VReg);
  return VReg;
}

// Calling Convention Implementation
#include "{{ Xpu }}GenCallingConv.inc"

SDValue
{{ Xpu }}TargetLowering::LowerFormalArguments(
  SDValue Chain,
  CallingConv::ID CallConv,
  bool IsVarArg,
  const SmallVectorImpl<ISD::InputArg> &Ins,
  const SDLoc &DL,
  SelectionDAG &DAG,
  SmallVectorImpl<SDValue> &InVals
) const {
  MachineFunction &MF = DAG.getMachineFunction();
  MachineFrameInfo &MFI = MF.getFrameInfo();

  std::vector<SDValue> OutChains;

  SmallVector<CCValAssign, 16> ArgLocs;
  CCState CCInfo(CallConv, IsVarArg, DAG.getMachineFunction(), ArgLocs, *DAG.getContext());
  CCInfo.AnalyzeFormalArguments(Ins, CC_{{ Xpu }}32);

  for (unsigned i = 0, e = ArgLocs.size(); i != e; ++i) {
    CCValAssign &VA = ArgLocs[i];
    EVT ValVT = VA.getValVT();
    bool IsRegLoc = VA.isRegLoc();
    if (IsRegLoc) {
      MVT RegVT = VA.getLocVT();
      unsigned ArgReg = VA.getLocReg();
      const TargetRegisterClass *RC = getRegClassFor(RegVT);

      unsigned Reg = addLiveIn(DAG.getMachineFunction(), ArgReg, RC);
      SDValue ArgValue = DAG.getCopyFromReg(Chain, DL, Reg, RegVT);

      if (VA.getLocInfo() != CCValAssign::Full) {
        unsigned Opcode = 0;
        if (VA.getLocInfo() == CCValAssign::SExt)
          Opcode = ISD::AssertSext;
        else if (VA.getLocInfo() == CCValAssign::ZExt)
          Opcode = ISD::AssertZext;
        if (Opcode)
          ArgValue = DAG.getNode(Opcode, DL, RegVT, ArgValue, DAG.getValueType(ValVT));
        ArgValue = DAG.getNode(ISD::TRUNCATE, DL, ValVT, ArgValue);
      }
      InVals.push_back(ArgValue);
    } else {
      MVT LocVT = VA.getLocVT();

      // Only arguments pased on the stack should make it here. 
      assert(VA.isMemLoc());

      int FI = MFI.CreateFixedObject(LocVT.getSizeInBits() / 8,
                                     VA.getLocMemOffset(), true);

      // Create load nodes to retrieve arguments from the stack
      SDValue FIN = DAG.getFrameIndex(FI, getPointerTy(DAG.getDataLayout()));
      SDValue ArgValue = DAG.getLoad(
          LocVT, DL, Chain, FIN,
          MachinePointerInfo::getFixedStack(DAG.getMachineFunction(), FI));
      OutChains.push_back(ArgValue.getValue(1));

      // ArgValue =
      //     UnpackFromArgumentSlot(ArgValue, VA, Ins[InsIdx].ArgVT, DL, DAG);

      InVals.push_back(ArgValue);
    }
  }

  if (IsVarArg) {
    static const MCPhysReg ArgIGPRs[] = {  // TODO: move to {{ Xpu }}CallingConv.cpp
      {{ arg_regs }}
    };
    ArrayRef<MCPhysReg> ArgRegs = ArrayRef(ArgIGPRs);
    unsigned Idx = CCInfo.getFirstUnallocated(ArgRegs);
    unsigned XLenInBytes = Subtarget.getXLen() / 8;
    MVT RegTy = MVT::getIntegerVT(XLenInBytes * 8);
    const TargetRegisterClass *RC = getRegClassFor(RegTy);
    MachineRegisterInfo &RegInfo = MF.getRegInfo();
    {{ Xpu }}MachineFunctionInfo *MFnInfo = MF.getInfo<{{ Xpu }}MachineFunctionInfo>();

    int VarArgsSaveSize = XLenInBytes * (ArgRegs.size() - Idx);
    int FI;

    if (ArgRegs.size() == Idx) {
      int VaArgOffset = CCInfo.getStackSize();
      FI = MFI.CreateFixedObject(XLenInBytes, VaArgOffset, true);
    } else {
      int VaArgOffset = -VarArgsSaveSize;
      FI = MFI.CreateFixedObject(VarArgsSaveSize, VaArgOffset, true);
      if (Idx % 2) {
        MFI.CreateFixedObject(
            XLenInBytes, VaArgOffset - static_cast<int>(XLenInBytes), true);
        VarArgsSaveSize += XLenInBytes;
      }

      SDValue FIN = DAG.getFrameIndex(FI, getPointerTy(DAG.getDataLayout()));

      for (unsigned I = Idx; I < ArgRegs.size(); ++I) {
        LLVM_DEBUG(dbgs() << "writeVarArgRegs I = " << I << '\n');
        const Register Reg = RegInfo.createVirtualRegister(RC);
        RegInfo.addLiveIn(ArgRegs[I], Reg);
        SDValue ArgValue = DAG.getCopyFromReg(Chain, DL, Reg, RegTy);
        SDValue Store =
            DAG.getStore(Chain, DL, ArgValue, FIN, MachinePointerInfo());
        OutChains.push_back(Store);
        FIN = DAG.getMemBasePlusOffset(FIN, TypeSize::getFixed(XLenInBytes), DL);
      }
    }

    MFnInfo->setVarArgsFrameIndex(FI);
    // MFnInfo->setVarArgsSaveSize(VarArgsSaveSize);
  }

  return Chain;
}

SDValue
{{ Xpu }}TargetLowering::LowerReturn(
  SDValue Chain,
  CallingConv::ID CallConv,
  bool IsVarArg,
  const SmallVectorImpl<ISD::OutputArg> &Outs,
  const SmallVectorImpl<SDValue> &OutVals,
  const SDLoc &DL,
  SelectionDAG &DAG
) const {
  MachineFunction &MF = DAG.getMachineFunction();
  SmallVector<CCValAssign, 16> RVLocs;

  CCState CCInfo(CallConv, IsVarArg, MF, RVLocs, *DAG.getContext());
  CCInfo.AnalyzeReturn(Outs, RetCC_{{ Xpu }}32);

  SDValue Glue;
  SmallVector<SDValue, 4> RetOps(1, Chain);
  for (unsigned i = 0; i != RVLocs.size(); ++i) {
    SDValue Val = OutVals[i];
    CCValAssign &VA = RVLocs[i];
    assert(VA.isRegLoc() && "Can only return in registers!");

    // if (VA.getLocInfo() == CCValAssign::BCvt)
    if (RVLocs[i].getValVT() != RVLocs[i].getLocVT())
      Val = DAG.getNode(ISD::BITCAST, DL, VA.getLocVT(), Val);

    Chain = DAG.getCopyToReg(Chain, DL, VA.getLocReg(), Val, Glue);

    Glue = Chain.getValue(1);
    RetOps.push_back(DAG.getRegister(VA.getLocReg(), VA.getLocVT()));
  }

  RetOps[0] = Chain; // Update chain.

  // Add the glue if we have it.
  if (Glue.getNode())
    RetOps.push_back(Glue);

  return DAG.getNode({{ Xpu }}ISD::RET_GLUE, DL, MVT::Other,
                     RetOps);
}

SDValue
{{ Xpu }}TargetLowering::LowerCall(
  CallLoweringInfo &CLI,
  SmallVectorImpl<SDValue> &InVals
) const {
  SelectionDAG &DAG = CLI.DAG;
  SDLoc &DL = CLI.DL;
  SmallVectorImpl<ISD::OutputArg> &Outs = CLI.Outs;
  SmallVectorImpl<SDValue> &OutVals = CLI.OutVals;
  SmallVectorImpl<ISD::InputArg> &Ins = CLI.Ins;
  SDValue Chain = CLI.Chain;
  SDValue Callee = CLI.Callee;
  bool &IsTailCall = CLI.IsTailCall;
  CallingConv::ID CallConv = CLI.CallConv;
  bool IsVarArg = CLI.IsVarArg;
  EVT PtrVT = getPointerTy(DAG.getDataLayout());

  MachineFunction &MF = DAG.getMachineFunction();

  SmallVector<CCValAssign, 16> ArgLocs;
  CCState ArgCCInfo(CallConv, IsVarArg, MF, ArgLocs, *DAG.getContext());
  ArgCCInfo.AnalyzeCallOperands(Outs, CC_{{ Xpu }}32);

  unsigned NumBytes = ArgCCInfo.getStackSize();

  if (!IsTailCall)
    Chain = DAG.getCALLSEQ_START(Chain, NumBytes, 0, CLI.DL);

  SmallVector<std::pair<Register, SDValue>, 8> RegsToPass;
  SmallVector<SDValue, 8> MemOpChains;
  SDValue StackPtr;
  for (unsigned i = 0, e = ArgLocs.size(); i != e; ++i) {
    CCValAssign &VA = ArgLocs[i];
    SDValue Arg = OutVals[i];
    MVT LocVT = VA.getLocVT();
    // ISD::ArgFlagsTy Flags = Outs[OutIdx].Flags;

    // if (VA.getLocInfo() == CCValAssign::Indirect) {
    // } else {
      switch (VA.getLocInfo()) {
        default: llvm_unreachable("Unknown loc info!");
              break;
        case CCValAssign::Full:
              break;
        case CCValAssign::SExt:
              Arg = DAG.getNode(ISD::SIGN_EXTEND, DL, LocVT, Arg);
              break;
        case CCValAssign::ZExt:
              Arg = DAG.getNode(ISD::ZERO_EXTEND, DL, LocVT, Arg);
              break;
        case CCValAssign::AExt:
              Arg = DAG.getNode(ISD::ANY_EXTEND, DL, LocVT, Arg);
              break;
      }
    // }

    if (VA.isRegLoc()) {
      RegsToPass.push_back(std::make_pair(VA.getLocReg(), Arg));
      continue;
    }

    assert(VA.isMemLoc() && "Argument not register or memory");
    /* MemOpChains.push_back(passArgOnStack(...)); */ {
      if (!IsTailCall) {
        SDValue PtrOff =
            DAG.getNode(ISD::ADD, DL, getPointerTy(DAG.getDataLayout()), StackPtr,
                        DAG.getIntPtrConstant(VA.getLocMemOffset(), DL));
        MemOpChains.push_back(DAG.getStore(Chain, DL, Arg, PtrOff, MachinePointerInfo()));
      } else {
        MachineFrameInfo &MFI = DAG.getMachineFunction().getFrameInfo();
        int FI = MFI.CreateFixedObject(Arg.getValueSizeInBits() / 8, VA.getLocMemOffset(), false);
        SDValue FIN = DAG.getFrameIndex(FI, getPointerTy(DAG.getDataLayout()));
        MemOpChains.push_back(DAG.getStore(Chain, DL, Arg, FIN, MachinePointerInfo()));
      }
    }
  }

  if (!MemOpChains.empty())
    Chain = DAG.getNode(ISD::TokenFactor, DL, MVT::Other, MemOpChains);

  SDValue Glue;

  // Build a sequence of copy-to-reg nodes, chained and glued together.
  for (auto &Reg : RegsToPass) {
    Chain = DAG.getCopyToReg(Chain, DL, Reg.first, Reg.second, Glue);
    Glue = Chain.getValue(1);
  }

  if (GlobalAddressSDNode *S = dyn_cast<GlobalAddressSDNode>(Callee)) {
    const GlobalValue *GV = S->getGlobal();
    Callee = DAG.getTargetGlobalAddress(GV, DL, PtrVT, 0, {{ Xpu }}II::MO_CALL);
  } else if (ExternalSymbolSDNode *S = dyn_cast<ExternalSymbolSDNode>(Callee)) {
    Callee = DAG.getTargetExternalSymbol(S->getSymbol(), PtrVT, {{ Xpu }}II::MO_CALL);
  }

  SmallVector<SDValue, 8> Ops;
  /* getOpndList(...) */ {
    Ops.push_back(Chain);
    Ops.push_back(Callee);

    for (auto &Reg : RegsToPass)
      Ops.push_back(DAG.getRegister(Reg.first, Reg.second.getValueType()));

    if (!IsTailCall) {
      const TargetRegisterInfo *TRI = Subtarget.getRegisterInfo();
      const uint32_t *Mask = TRI->getCallPreservedMask(MF, CallConv);
      assert(Mask && "Missing call preserved mask for calling convention");
      Ops.push_back(DAG.getRegisterMask(Mask));
    }

    if (Glue.getNode())
      Ops.push_back(Glue);
  }

  // Emit the call.
  SDVTList NodeTys = DAG.getVTList(MVT::Other, MVT::Glue);

  if (IsTailCall) {
    // return DAG.getNode({{ Xpu }}ISD::TailCall, DL, MVT::Other, Ops);
  }

  Chain = DAG.getNode({{ Xpu }}ISD::CALL, DL, NodeTys, Ops);
  Glue = Chain.getValue(1);

  Chain = DAG.getCALLSEQ_END(Chain, NumBytes, 0, Glue, DL);
  Glue = Chain.getValue(1);

  /* return LowerCallResult(...); */ {
    SmallVector<CCValAssign, 16> RVLocs;
    CCState RetCCInfo(CallConv, IsVarArg, MF, RVLocs, *DAG.getContext());
    RetCCInfo.AnalyzeCallResult(Ins, RetCC_{{ Xpu }}32);

    for (unsigned i = 0; i != RVLocs.size(); ++i) {
      SDValue Val = DAG.getCopyFromReg(Chain, DL, RVLocs[i].getLocReg(),
                                      RVLocs[i].getLocVT(), Glue);
      Chain = Val.getValue(1);
      Glue = Val.getValue(2);

      if (RVLocs[i].getValVT() != RVLocs[i].getLocVT())
        Val = DAG.getNode(ISD::BITCAST, DL, RVLocs[i].getValVT(), Val);

      InVals.push_back(Val);
    }
  }
  return Chain;
}

SDValue
{{ Xpu }}TargetLowering::LowerOperation(
  SDValue Op,
  SelectionDAG &DAG
) const {
  switch (Op.getOpcode()) {
  default:
    report_fatal_error("unimplemented operand");
  case ISD::GlobalAddress:
    return lowerGlobalAddress(Op, DAG);
  case ISD::ConstantPool:
    return lowerConstantPool(Op, DAG);
  case ISD::SELECT:
    return lowerSELECT(Op, DAG);
  case ISD::VASTART:
    return lowerVASTART(Op, DAG);
  }
}

static SDValue getTargetNode(GlobalAddressSDNode *N, const SDLoc &DL, EVT Ty,
                             SelectionDAG &DAG, unsigned Flags) {
  return DAG.getTargetGlobalAddress(N->getGlobal(), DL, Ty, 0, Flags);
}

static SDValue getTargetNode(BlockAddressSDNode *N, const SDLoc &DL, EVT Ty,
                             SelectionDAG &DAG, unsigned Flags) {
  return DAG.getTargetBlockAddress(N->getBlockAddress(), Ty, N->getOffset(),
                                   Flags);
}

static SDValue getTargetNode(ConstantPoolSDNode *N, const SDLoc &DL, EVT Ty,
                             SelectionDAG &DAG, unsigned Flags) {
  return DAG.getTargetConstantPool(N->getConstVal(), Ty, N->getAlign(),
                                   N->getOffset(), Flags);
}

static SDValue getTargetNode(JumpTableSDNode *N, const SDLoc &DL, EVT Ty,
                             SelectionDAG &DAG, unsigned Flags) {
  return DAG.getTargetJumpTable(N->getIndex(), Ty, Flags);
}

template <class NodeTy>
SDValue
{{ Xpu }}TargetLowering::getAddr(
  NodeTy *N,
  SelectionDAG &DAG,
  bool IsLocal,
  bool IsExternWeak
) const {
  SDLoc DL(N);
  EVT Ty = getPointerTy(DAG.getDataLayout());
  MVT XLenVT = Subtarget.getXLenVT();

  if (isPositionIndependent()) {
    SDValue Addr = getTargetNode(N, DL, Ty, DAG, 0);
    if (IsLocal)
      // return DAG.getNode(CustomXPUISD::LLA, DL, Ty, Addr);
      return SDValue(DAG.getMachineNode({{ Xpu }}::ADDI, DL, Ty,
                                        DAG.getRegister({{ Xpu }}::X0, XLenVT), Addr), 0);
  }

  // switch (getTargetMachine().getCodeModel()) {
  //   default:
  //     report_fatal_error("Unsupported code model for lowering");
  //   case CodeModel::Small: {
      SDValue AddrHi = getTargetNode(N, DL, Ty, DAG, {{ Xpu }}II::MO_SYMBOL);
      SDValue AddrLo = getTargetNode(N, DL, Ty, DAG, {{ Xpu }}II::MO_SYMBOL);
      SDValue MNHi = SDValue(DAG.getMachineNode({{ Xpu }}::LUI, DL, Ty, AddrHi), 0);
      return SDValue(DAG.getMachineNode({{ Xpu }}::ADDI, DL, Ty, MNHi, AddrLo), 0);
  //   }
  //   case CodeModel::Medium: {
  //     SDValue Addr = getTargetNode(N, DL, Ty, DAG, 0);
  //     return SDValue(DAG.getMachineNode({{ Xpu }}::PseudoLLA, DL, Ty, Addr), 0);
  //   }
  // }
}

SDValue
{{ Xpu }}TargetLowering::lowerGlobalAddress(
  SDValue Op,
  SelectionDAG &DAG
) const {
  GlobalAddressSDNode *N = cast<GlobalAddressSDNode>(Op);
  int64_t Offset = N->getOffset();
  SDLoc DL(Op);
  EVT Ty = Op.getValueType();
  MVT XLenVT = Subtarget.getXLenVT();
  // assert(N->getOffset() == 0 && "unexpected offset in global node");
  const GlobalValue *GV = N->getGlobal();
  SDValue Addr = getAddr(N, DAG, GV->isDSOLocal(), GV->hasExternalWeakLinkage());
  if (Offset) {
    return DAG.getNode(ISD::ADD, DL, Ty, Addr,
                        DAG.getConstant(Offset, DL, XLenVT));
  } else {
    return Addr;
  }
}

SDValue
{{ Xpu }}TargetLowering::lowerConstantPool(
  SDValue Op,
  SelectionDAG &DAG
) const {
  ConstantPoolSDNode *N = cast<ConstantPoolSDNode>(Op);
  return getAddr(N, DAG);
}

SDValue
{{ Xpu }}TargetLowering::lowerSELECT(
  SDValue Op,
  SelectionDAG &DAG
) const {
  SDValue CondV = Op.getOperand(0);
  SDValue TrueV = Op.getOperand(1);
  SDValue FalseV = Op.getOperand(2);
  SDLoc DL(Op);
  MVT VT = Op.getSimpleValueType();
  MVT XLenVT = Subtarget.getXLenVT();

  // (select condv, truev, falsev) -> (SELECT condv, 0, setne, truev, falsev)
  SDValue Zero = DAG.getConstant(0, DL, XLenVT);
  // SDValue SetNE = DAG.getCondCode(ISD::SETNE);
  SDValue SetNE = DAG.getConstant(ISD::SETNE, DL, XLenVT);

  SDValue Ops[] = {CondV, Zero, SetNE, TrueV, FalseV};

  return DAG.getNode({{ Xpu }}ISD::SELECT_CC, DL, VT, Ops);
}

SDValue
{{ Xpu }}TargetLowering::lowerVASTART(
  SDValue Op,
  SelectionDAG &DAG
) const {
  MachineFunction &MF = DAG.getMachineFunction();
  {{ Xpu }}MachineFunctionInfo *FuncInfo = MF.getInfo<{{ Xpu }}MachineFunctionInfo>();

  SDLoc DL = SDLoc(Op);
  SDValue FI = DAG.getFrameIndex(FuncInfo->getVarArgsFrameIndex(),
                                 getPointerTy(MF.getDataLayout()));

  // vastart just stores the address of the VarArgsFrameIndex slot into the
  // memory location argument.
  const Value *SV = cast<SrcValueSDNode>(Op.getOperand(2))->getValue();
  return DAG.getStore(Op.getOperand(0), DL, FI, Op.getOperand(1),
                      MachinePointerInfo(SV));
}

const char *
{{ Xpu }}TargetLowering::getTargetNodeName(
  unsigned Opcode
) const {
  switch (({{ Xpu }}ISD::NodeType)Opcode) {
  case {{ Xpu }}ISD::FIRST_NUMBER:
    break;
  case {{ Xpu }}ISD::RET_GLUE:
    return "{{ Xpu }}ISD::RET_GLUE";
  case {{ Xpu }}ISD::CALL:
    return "{{ Xpu }}ISD::CALL";
  case {{ Xpu }}ISD::SELECT_CC:
    return "{{ Xpu }}ISD::SELECT_CC";
  case {{ Xpu }}ISD::BR_CC:
    return "{{ Xpu }}ISD::BR_CC";
  case {{ Xpu }}ISD::Wrapper:
    return "{{ Xpu }}ISD::Wrapper";
  case {{ Xpu }}ISD::MEMCPY:
    return "{{ Xpu }}ISD::MEMCPY";
  }
  return nullptr;
}

static unsigned
getBranchOpcodeForIntCondCode (ISD::CondCode CC) {
  switch (CC) {
  default:
    llvm_unreachable("Unsupported CondCode");
  case ISD::SETEQ:
    return {{ Xpu }}::BEQ;
  case ISD::SETNE:
    return {{ Xpu }}::BNE;
  case ISD::SETLT:
    return {{ Xpu }}::BLT;
  case ISD::SETGE:
    return {{ Xpu }}::BGE;
  case ISD::SETULT:
    return {{ Xpu }}::BLTU;
  case ISD::SETUGE:
    return {{ Xpu }}::BGEU;
  }
}

static MachineBasicBlock *emitSelectPseudo(
  MachineInstr &MI,
  MachineBasicBlock *BB,
  const {{ Xpu }}Subtarget &Subtarget
) {
  const TargetInstrInfo &TII = *Subtarget.getInstrInfo();
  const BasicBlock *LLVM_BB = BB->getBasicBlock();
  DebugLoc DL = MI.getDebugLoc();
  MachineFunction::iterator I = ++BB->getIterator();

  MachineBasicBlock *HeadMBB = BB;
  MachineFunction *F = BB->getParent();
  MachineBasicBlock *TailMBB = F->CreateMachineBasicBlock(LLVM_BB);
  MachineBasicBlock *IfFalseMBB = F->CreateMachineBasicBlock(LLVM_BB);

  F->insert(I, IfFalseMBB);
  F->insert(I, TailMBB);

  TailMBB->splice(TailMBB->begin(), HeadMBB,
                  std::next(MachineBasicBlock::iterator(MI)), HeadMBB->end());

  TailMBB->transferSuccessorsAndUpdatePHIs(HeadMBB);
  HeadMBB->addSuccessor(IfFalseMBB);
  HeadMBB->addSuccessor(TailMBB);

  unsigned LHS = MI.getOperand(1).getReg();
  unsigned RHS = MI.getOperand(2).getReg();
  auto CC = static_cast<ISD::CondCode>(MI.getOperand(3).getImm());
  unsigned Opcode = getBranchOpcodeForIntCondCode(CC);

  BuildMI(HeadMBB, DL, TII.get(Opcode))
    .addReg(LHS)
    .addReg(RHS)
    .addMBB(TailMBB);

  IfFalseMBB->addSuccessor(TailMBB);

  // %Result = phi [ %TrueValue, HeadMBB ], [ %FalseValue, IfFalseMBB ]
  BuildMI(*TailMBB, TailMBB->begin(), DL, TII.get({{ Xpu }}::PHI),
          MI.getOperand(0).getReg())
      .addReg(MI.getOperand(4).getReg())
      .addMBB(HeadMBB)
      .addReg(MI.getOperand(5).getReg())
      .addMBB(IfFalseMBB);

  MI.eraseFromParent();
  return TailMBB;
}

MachineBasicBlock *
{{ Xpu }}TargetLowering::EmitInstrWithCustomInserter(
  MachineInstr &MI,
  MachineBasicBlock *BB
) const {
  switch (MI.getOpcode()) {
  default:
    llvm_unreachable("Unexpected instr type to insert");
  case {{ Xpu }}::Select_GPR:
    return emitSelectPseudo(MI, BB, Subtarget);
  }
}
