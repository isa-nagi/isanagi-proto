//===-- {{ Xpu }}.td - Describe the {{ Xpu }} Target Machine *- tablegen -*-===//

include "llvm/Target/Target.td"

include "{{ Xpu }}Features.td"

def Feature64Bit : SubtargetFeature<"64bit", "Has64Bit", "true",
                                    "Enable 64-bit instructions">;
def FeatureBE : SubtargetFeature<"bigendian", "HasBigEndian", "true",
                                 "Enable Big-endian byte order">;

{% for processor in processors %}
def {{ processor.varname }} : ProcessorModel<"{{ processor.name }}", NoSchedModel, [
  {%- for feature in processor.features %}
  Feature_{{ feature.varname }}{%if not loop.last %},{% endif %}
  {%- endfor %}
]>;
{%- endfor %}

include "{{ Xpu }}RegisterInfo.td"
include "{{ Xpu }}CallingConv.td"
include "{{ Xpu }}Schedule.td"
include "{{ Xpu }}InstrInfo.td"

def {{ Xpu }}InstrInfo : InstrInfo {
}

def {{ Xpu }}AsmParser : AsmParser {
  let ShouldEmitMatchRegisterAltName = 1;
  let AllowDuplicateRegisterNames = 1;
}

def {{ Xpu }}AsmWriter : AsmWriter {
  int PassSubtarget = 1;
}

def {{ Xpu }} : Target {
  let InstructionSet = {{ Xpu }}InstrInfo;
  let AssemblyParsers = [{{ Xpu }}AsmParser];
  let AssemblyWriters = [{{ Xpu }}AsmWriter];
  let AllowRegisterRenaming = 1;
}
