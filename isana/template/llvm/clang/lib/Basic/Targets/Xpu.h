#ifndef LLVM_CLANG_LIB_BASIC_TARGETS_{{ XPU }}_H
#define LLVM_CLANG_LIB_BASIC_TARGETS_{{ XPU }}_H

#include "clang/Basic/TargetInfo.h"
#include "clang/Basic/TargetOptions.h"
#include "llvm/Support/Compiler.h"
#include "llvm/TargetParser/Triple.h"
#include <optional>

namespace clang {
namespace targets {

class {{ Xpu }}TargetInfo : public TargetInfo {
protected:
  std::string ABI, CPU;

public:
  {{ Xpu }}TargetInfo(const llvm::Triple &Triple, const TargetOptions &)
      : TargetInfo(Triple) {
    BFloat16Width = 16;
    BFloat16Align = 16;
    BFloat16Format = &llvm::APFloat::BFloat();
    LongDoubleWidth = 128;
    LongDoubleAlign = 128;
    LongDoubleFormat = &llvm::APFloat::IEEEquad();
    SuitableAlign = 128;
    WCharType = SignedInt;
    WIntType = UnsignedInt;
    MCountName = "_mcount";
    HasFloat16 = true;
    HasStrictFP = true;
  }

  bool setCPU(const std::string &Name) override {
    if (!isValidCPUName(Name))
      return false;
    CPU = Name;
    return true;
  }

  StringRef getABI() const override { return ABI; }
  bool setABI(const std::string &Name) override;
  void getTargetDefines(const LangOptions &Opts,
                        MacroBuilder &Builder) const override;

  ArrayRef<Builtin::Info> getTargetBuiltins() const override;

  BuiltinVaListKind getBuiltinVaListKind() const override {
    return TargetInfo::VoidPtrBuiltinVaList;
  }

  std::string_view getClobbers() const override { return ""; }

  StringRef getConstraintRegister(StringRef Constraint,
                                  StringRef Expression) const override {
    return Expression;
  }

  ArrayRef<const char *> getGCCRegNames() const override;

  int getEHDataRegisterNumber(unsigned RegNo) const override;

  ArrayRef<TargetInfo::GCCRegAlias> getGCCRegAliases() const override;

  bool validateAsmConstraint(const char *&Name,
                             TargetInfo::ConstraintInfo &Info) const override;

  bool hasFeature(StringRef Feature) const override;

  bool hasBitIntType() const override { return true; }

  bool hasBFloat16Type() const override { return true; }

  bool useFP16ConversionIntrinsics() const override {
    return false;
  }

  bool isValidCPUName(StringRef Name) const override;
  bool supportsTargetAttributeTune() const override { return true; }

  std::pair<unsigned, unsigned> hardwareInterferenceSizes() const override {
    return std::make_pair(32, 32);
  }

  bool supportsCpuSupports() const override { return getTriple().isOSLinux(); }
  bool supportsCpuInit() const override { return getTriple().isOSLinux(); }
};

class LLVM_LIBRARY_VISIBILITY {{ Xpu }}32leTargetInfo : public {{ Xpu }}TargetInfo {
public:
  {{ Xpu }}32leTargetInfo(const llvm::Triple &Triple, const TargetOptions &Opts)
      : {{ Xpu }}TargetInfo(Triple, Opts) {
    BigEndian = false;
    IntPtrType = SignedInt;
    PtrDiffType = SignedInt;
    SizeType = UnsignedInt;
    resetDataLayout("e-m:e-p:32:32-i32:32-n32-S128");
  }
};

class LLVM_LIBRARY_VISIBILITY {{ Xpu }}32beTargetInfo : public {{ Xpu }}TargetInfo {
public:
  {{ Xpu }}32beTargetInfo(const llvm::Triple &Triple, const TargetOptions &Opts)
      : {{ Xpu }}TargetInfo(Triple, Opts) {
    BigEndian = true;
    IntPtrType = SignedInt;
    PtrDiffType = SignedInt;
    SizeType = UnsignedInt;
    resetDataLayout("E-m:e-p:32:32-i32:32-n32-S128");
  }
};

class LLVM_LIBRARY_VISIBILITY {{ Xpu }}64leTargetInfo : public {{ Xpu }}TargetInfo {
public:
  {{ Xpu }}64leTargetInfo(const llvm::Triple &Triple, const TargetOptions &Opts)
      : {{ Xpu }}TargetInfo(Triple, Opts) {
    BigEndian = false;
    IntPtrType = SignedInt;
    PtrDiffType = SignedInt;
    SizeType = UnsignedInt;
    resetDataLayout("e-m:e-p:64:64-i64:64-n32:64-S128");
  }
};

class LLVM_LIBRARY_VISIBILITY {{ Xpu }}64beTargetInfo : public {{ Xpu }}TargetInfo {
public:
  {{ Xpu }}64beTargetInfo(const llvm::Triple &Triple, const TargetOptions &Opts)
      : {{ Xpu }}TargetInfo(Triple, Opts) {
    BigEndian = true;
    IntPtrType = SignedInt;
    PtrDiffType = SignedInt;
    SizeType = UnsignedInt;
    resetDataLayout("E-m:e-p:64:64-i64:64-n32:64-S128");
  }
};
} // namespace targets
} // namespace clang

#endif // LLVM_CLANG_LIB_BASIC_TARGETS_{{ XPU }}_H
