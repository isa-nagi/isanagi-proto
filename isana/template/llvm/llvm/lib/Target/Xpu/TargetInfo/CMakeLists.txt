add_llvm_component_library(LLVM{{ Xpu }}Info
  {{ Xpu }}TargetInfo.cpp

  LINK_COMPONENTS
  MC
  Support

  ADD_TO_COMPONENT
  {{ Xpu }}
)
