from typing_extensions import Annotated, Literal, TypedDict


class CoordinatorRouter(TypedDict):
    """Decide to route to next step between data_collector and __end__"""

    next: Literal["data_collector", "__end__"]
    generated: Annotated[
        str,
        ...,
        "Empty if next is data_collector, a generated answer if next is __end__",
    ]
