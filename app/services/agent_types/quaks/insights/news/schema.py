from typing_extensions import Annotated, Literal, TypedDict


class CoordinatorRouter(TypedDict):
    """Decide to route to next step between aggregator and __end__"""

    next: Literal["aggregator", "__end__"]
    generated: Annotated[
        str,
        ...,
        "Empty if next is aggregator, a generated answer if next is __end__",
    ]
