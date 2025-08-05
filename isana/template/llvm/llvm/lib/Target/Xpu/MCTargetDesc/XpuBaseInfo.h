//===- {{ Xpu }}BaseInfo.h - Top level definitions for {{ Xpu }} MC -===//
//
// This file contains small standalone enum definitions for the {{ Xpu }} target
// useful for the compiler back-end and the MC libraries.
//
//===----------------------------------------------------------------------===//
#ifndef LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}BASEINFO_H
#define LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}BASEINFO_H

#include "MCTargetDesc/{{ Xpu }}MCTargetDesc.h"
#include "llvm/ADT/APFloat.h"
#include "llvm/ADT/APInt.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/ADT/StringSwitch.h"
#include "llvm/MC/MCInstrDesc.h"

namespace llvm {

// {{ Xpu }}II - This namespace holds all of the target specific flags that
// instruction info tracks.
namespace {{ Xpu }}II {
// {{ Xpu }} Specific Machine Operand Flags
enum {
  MO_None = 0,
  {%- for expr in asm_call_exprs + asm_other_exprs %}
  MO_{{ expr.name.upper() }},  // {{ expr.src }}
  {%- endfor %}
};
} // namespace {{ Xpu }}II

} // namespace llvm

#endif // LLVM_LIB_TARGET_{{ XPU }}_MCTARGETDESC_{{ XPU }}BASEINFO_H

