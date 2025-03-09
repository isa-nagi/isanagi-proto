#include "{{ Xpu }}.h"
#include "Targets.h"
#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/MacroBuilder.h"
#include "clang/Basic/TargetBuiltins.h"
#include "llvm/ADT/StringSwitch.h"

using namespace clang;
using namespace clang::targets;

static constexpr Builtin::Info BuiltinInfo[] = {
#define BUILTIN(ID, TYPE, ATTRS)                                               \
  { #ID, TYPE, ATTRS, nullptr, HeaderDesc::NO_HEADER, ALL_LANGUAGES},
#define TARGET_BUILTIN(ID, TYPE, ATTRS, FEATURE)                               \
  { #ID, TYPE, ATTRS, FEATURE, HeaderDesc::NO_HEADER, ALL_LANGUAGES},
#include "clang/Basic/Builtins{{ Xpu }}.def"
};

static constexpr llvm::StringLiteral ValidCPUNames[] = {
    {"{{ xpu }}32le"}
};

bool {{ Xpu }}TargetInfo::setABI(const std::string &Name) {
  if (Name == "abi32") {
    ABI = Name;
    return true;
  }
  return false;
}

bool {{ Xpu }}TargetInfo::isValidCPUName(StringRef Name) const {
  return llvm::find(ValidCPUNames, Name) != std::end(ValidCPUNames);
}

void {{ Xpu }}TargetInfo::getTargetDefines(const LangOptions &Opts,
                                             MacroBuilder &Builder) const {
  Builder.defineMacro("__{{ xpu }}__");
  Builder.defineMacro("__{{ xpu }}32__");
  Builder.defineMacro("__{{ xpu }}32le__");
  if (Opts.GNUMode)
    Builder.defineMacro("{{ xpu }}32le");
}

bool {{ Xpu }}TargetInfo::hasFeature(StringRef Feature) const {
  return llvm::StringSwitch<bool>(Feature)
      .Case("{{ xpu }}32le", true)
      .Default(false);
}

ArrayRef<Builtin::Info> {{ Xpu }}TargetInfo::getTargetBuiltins() const {
  return llvm::ArrayRef(BuiltinInfo, clang::{{ Xpu }}::LastTSBuiltin -
                                             Builtin::FirstTSBuiltin);
}

ArrayRef<const char *> {{ Xpu }}TargetInfo::getGCCRegNames() const {
  static const char *const GCCRegNames[] = {
      "x0",
  };
  return llvm::ArrayRef(GCCRegNames);
}

ArrayRef<TargetInfo::GCCRegAlias> {{ Xpu }}TargetInfo::getGCCRegAliases() const {
  static const TargetInfo::GCCRegAlias GCCRegAliases[] = {
      { {"zero"}, "x0"},
  };
  return llvm::ArrayRef(GCCRegAliases);
}

bool {{ Xpu }}TargetInfo::validateAsmConstraint(
    const char *&Name, TargetInfo::ConstraintInfo &Info) const {
    return false;
}
