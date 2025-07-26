//===- {{ Xpu }}.cpp -===//

#include "Symbols.h"
#include "Target.h"
#include "lld/Common/ErrorHandler.h"
#include "llvm/BinaryFormat/ELF.h"
#include "llvm/Support/Endian.h"

using namespace llvm;
using namespace llvm::object;
using namespace llvm::support::endian;
using namespace llvm::ELF;
using namespace lld;
using namespace lld::elf;

namespace {
class {{ Xpu }} final : public TargetInfo {
public:
  {{ Xpu }}();
  RelExpr getRelExpr(RelType type, const Symbol &s,
                     const uint8_t *loc) const override;
  void relocate(uint8_t *loc, const Relocation &rel,
                uint64_t val) const override;
};
} // namespace

{{ Xpu }}::{{ Xpu }}() {
}

RelExpr {{ Xpu }}::getRelExpr(RelType type, const Symbol &s,
                           const uint8_t *loc) const {
  switch (type) {
  {% for fx in fixups_pc_rel -%}
  case R_{{ XPU }}_{{ fx.name.upper() }}:
  {% endfor %}  return R_PC;
  default:
    return R_ABS;
  }
}

void {{ Xpu }}::relocate(uint8_t *loc, const Relocation &rel, uint64_t val) const {
  switch (rel.type) {
  case R_{{ XPU }}_32: {
    write32le(loc, val);
    return;
  }
  case R_{{ XPU }}_64: {
    write64le(loc, val);
    return;
  }
  {% for fx in fixup_relocs -%}
  case R_{{ XPU }}_{{ fx.name.upper() }}: {
    val = {{ fx.val_carryed }};
    uint32_t newval = read{{ fx.size }}le(loc)
    {% for proc in fx.reloc_procs -%}
    {{ proc }}
    {% endfor -%}
    ;
    write{{ fx.size }}le(loc, newval);
    break; }
  {% endfor %}
  default:
    error(getErrorLocation(loc) + "unrecognized relocation " +
          toString(rel.type));
  }
}

TargetInfo *elf::get{{ Xpu }}TargetInfo() {
  static {{ Xpu }} target;
  return &target;
}
