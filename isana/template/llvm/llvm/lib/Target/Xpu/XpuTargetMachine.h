//===-- {{ Xpu }}TargetMachine.h - Define TargetMachine for {{ Xpu }} --===//

#ifndef LLVM_LIB_TARGET_{{ XPU }}_{{ XPU }}TARGETMACHINE_H
#define LLVM_LIB_TARGET_{{ XPU }}_{{ XPU }}TARGETMACHINE_H

#include "{{ Xpu }}Subtarget.h"
#include "llvm/CodeGen/SelectionDAGTargetInfo.h"
#include "llvm/IR/DataLayout.h"
#include "llvm/Target/TargetMachine.h"
#include <optional>

namespace llvm {
class {{ Xpu }}TargetMachine : public LLVMTargetMachine {
  std::unique_ptr<TargetLoweringObjectFile> TLOF;
  {{ Xpu }}Subtarget Subtarget;

public:
  {{ Xpu }}TargetMachine(const Target &T, const Triple &TT, StringRef CPU,
                         StringRef FS, const TargetOptions &Options,
                         std::optional<Reloc::Model> RM,
                         std::optional<CodeModel::Model> CM, CodeGenOptLevel OL,
                         bool JIT);

  const {{ Xpu }}Subtarget *getSubtargetImpl() const { return &Subtarget; }
  const {{ Xpu }}Subtarget *getSubtargetImpl(const Function &) const override {
    return &Subtarget;
  }

  TargetPassConfig *createPassConfig(PassManagerBase &PM) override;

  TargetLoweringObjectFile *getObjFileLowering() const override {
    return TLOF.get();
  }

  MachineFunctionInfo *
  createMachineFunctionInfo(BumpPtrAllocator &Allocator, const Function &F,
                            const TargetSubtargetInfo *STI) const override;
};
} // namespace llvm

#endif
