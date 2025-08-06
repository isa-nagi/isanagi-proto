add_llvm_component_group({{ Xpu }})

set(LLVM_TARGET_DEFINITIONS {{ Xpu }}.td)

tablegen(LLVM {{ Xpu }}GenAsmMatcher.inc -gen-asm-matcher)
tablegen(LLVM {{ Xpu }}GenAsmWriter.inc -gen-asm-writer)
tablegen(LLVM {{ Xpu }}GenCallingConv.inc -gen-callingconv)
tablegen(LLVM {{ Xpu }}GenDAGISel.inc -gen-dag-isel)
tablegen(LLVM {{ Xpu }}GenDisassemblerTables.inc -gen-disassembler)
# tablegen(LLVM {{ Xpu }}GenGlobalISel.inc -gen-global-isel)
# tablegen(LLVM {{ Xpu }}GenPreLegalizeGICombiner.inc -gen-global-isel-combiner
#               -combiners="{{ Xpu }}PreLegalizerCombiner")
# tablegen(LLVM {{ Xpu }}GenPostLegalizeGICombiner.inc -gen-global-isel-combiner
#               -combiners="{{ Xpu }}PostLegalizerCombiner")
tablegen(LLVM {{ Xpu }}GenInstrInfo.inc -gen-instr-info)
tablegen(LLVM {{ Xpu }}GenMCCodeEmitter.inc -gen-emitter)
tablegen(LLVM {{ Xpu }}GenMCPseudoLowering.inc -gen-pseudo-lowering)
# tablegen(LLVM {{ Xpu }}GenRegisterBank.inc -gen-register-bank)
tablegen(LLVM {{ Xpu }}GenRegisterInfo.inc -gen-register-info)
# tablegen(LLVM {{ Xpu }}GenSearchableTables.inc -gen-searchable-tables)
tablegen(LLVM {{ Xpu }}GenSubtargetInfo.inc -gen-subtarget)

add_public_tablegen_target({{ Xpu }}CommonTableGen)

add_llvm_target({{ Xpu }}CodeGen
  {{ Xpu }}AsmPrinter.cpp
  # {{ Xpu }}CodeGenPrepare.cpp
  # {{ Xpu }}DeadRegisterDefinitions.cpp
  # {{ Xpu }}MakeCompressible.cpp
  # {{ Xpu }}ExpandAtomicPseudoInsts.cpp
  {{ Xpu }}ExpandPseudoInsts.cpp
  {{ Xpu }}FrameLowering.cpp
  # {{ Xpu }}GatherScatterLowering.cpp
  # {{ Xpu }}IndirectBranchTracking.cpp
  # {{ Xpu }}InsertVSETVLI.cpp
  # {{ Xpu }}InsertReadWriteCSR.cpp
  # {{ Xpu }}InsertWriteVXRM.cpp
  {{ Xpu }}InstrInfo.cpp
  {{ Xpu }}ISelDAGToDAG.cpp
  {{ Xpu }}ISelLowering.cpp
  # {{ Xpu }}LandingPadSetup.cpp
  {{ Xpu }}MachineFunctionInfo.cpp
  # {{ Xpu }}MergeBaseOffset.cpp
  # {{ Xpu }}OptWInstrs.cpp
  # {{ Xpu }}RedundantCopyElimination.cpp
  # {{ Xpu }}MoveMerger.cpp
  # {{ Xpu }}PushPopOptimizer.cpp
  {{ Xpu }}RegisterInfo.cpp
  {{ Xpu }}Subtarget.cpp
  {{ Xpu }}TargetMachine.cpp
  # {{ Xpu }}TargetObjectFile.cpp
  # {{ Xpu }}TargetTransformInfo.cpp
  # {{ Xpu }}VectorPeephole.cpp
  # GISel/{{ Xpu }}CallLowering.cpp
  # GISel/{{ Xpu }}InstructionSelector.cpp
  # GISel/{{ Xpu }}LegalizerInfo.cpp
  # GISel/{{ Xpu }}PostLegalizerCombiner.cpp
  # GISel/{{ Xpu }}O0PreLegalizerCombiner.cpp
  # GISel/{{ Xpu }}PreLegalizerCombiner.cpp
  # GISel/{{ Xpu }}RegisterBankInfo.cpp

  LINK_COMPONENTS
  Analysis
  AsmPrinter
  CodeGen
  CodeGenTypes
  Core
  GlobalISel
  IPO
  MC
  {{ Xpu }}Desc
  {{ Xpu }}Info
  Scalar
  SelectionDAG
  Support
  Target
  TargetParser
  TransformUtils
  Vectorize

  ADD_TO_COMPONENT
  {{ Xpu }}
  )

add_subdirectory(AsmParser)
add_subdirectory(Disassembler)
add_subdirectory(MCTargetDesc)
add_subdirectory(TargetInfo)

