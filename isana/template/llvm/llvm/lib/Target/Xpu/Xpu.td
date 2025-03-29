//===-- {{ Xpu }}.td - Describe the {{ Xpu }} Target Machine *- tablegen -*-===//

include "llvm/Target/Target.td"

def Feature64Bit : SubtargetFeature<"64bit", "Has64Bit", "true",
                                    "Enable 64-bit instructions">;
def FeatureBE : SubtargetFeature<"bigendian", "HasBigEndian", "true",
                                 "Enable Big-endian byte order">;
def ProcXPU32le : ProcessorModel<"xpu-32le", NoSchedModel, []>;
def ProcXPU32be : ProcessorModel<"xpu-32be", NoSchedModel, [FeatureBE]>;
def ProcXPU64le : ProcessorModel<"xpu-64le", NoSchedModel, [Feature64Bit]>;
def ProcXPU64be : ProcessorModel<"xpu-64be", NoSchedModel, [Feature64Bit, FeatureBE]>;

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
