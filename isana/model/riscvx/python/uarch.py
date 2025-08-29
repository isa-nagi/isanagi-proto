from isana.uarch import Processor

xpu32le = Processor(
    name="xpu32le",
    subsets=(
        "rv32",
        "ext-m",
        "ext-zifencei",
        "ext-zicsr",
    ),
)

xpu32be = Processor(
    name="xpu32be",
    subsets=(
        "rv32",
        "big-endian",
        "ext-m",
        "ext-zifencei",
        "ext-zicsr",
    ),
)

xpu64le = Processor(
    name="xpu64le",
    subsets=(
        "rv64",
        "ext-m",
        "ext-zifencei",
        "ext-zicsr",
    ),
)

xpu64be = Processor(
    name="xpu64be",
    subsets=(
        "rv64",
        "big-endian",
        "ext-m",
        "ext-zifencei",
        "ext-zicsr",
    ),
)

processors = [
    xpu32le,
    xpu32be,
    xpu64le,
    xpu64be,
]
