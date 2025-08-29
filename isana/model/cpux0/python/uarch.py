from isana.uarch import Processor

cpux0 = Processor(
    name="cpux0",
    subsets=[],
)

cpux0ii = Processor(
    name="cpux0II",
    subsets=["cpu0II"],
)

processors = [
    cpux0,
    cpux0ii,
]
