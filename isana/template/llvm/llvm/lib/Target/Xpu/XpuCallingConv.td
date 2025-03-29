//===-- {{ Xpu }}CallingConv.td - Calling Conventions {{ Xpu }} --------*- tablegen -*-===//

def CSR_ABI0 : CalleeSavedRegs<(add {{ callee_saved_regs|join(', ') }})>;

def CC_{{ Xpu }}32 : CallingConv<[
  // Promote i8/i16 args to i32
  CCIfType<[i8, i16], CCPromoteToType<i32>>,
  CCIfType<[i32], CCAssignToReg<[{{ arg_regs|join(', ') }}]>>,
  CCIfType<[i32], CCAssignToStack<4, 4>>
]>;

def RetCC_{{ Xpu }}32 : CallingConv<[
  CCIfType<[i8, i16], CCPromoteToType<i32>>,
  CCIfType<[i32], CCAssignToReg<[{{ ret_regs|join(', ') }}]>>
]>;

def CC_{{ Xpu }}64 : CallingConv<[
  // Promote i8/i16/i32 args to i64
  CCIfType<[i8, i16, i32], CCPromoteToType<i64>>,
  CCIfType<[i64], CCAssignToReg<[{{ arg_regs|join(', ') }}]>>,
  CCIfType<[i64], CCAssignToStack<8, 8>>
]>;

def RetCC_{{ Xpu }}64 : CallingConv<[
  CCIfType<[i8, i16, i32], CCPromoteToType<i64>>,
  CCIfType<[i64], CCAssignToReg<[{{ ret_regs|join(', ') }}]>>
]>;
