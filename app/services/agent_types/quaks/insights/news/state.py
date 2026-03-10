from langgraph.graph import MessagesState
from langgraph.managed import RemainingSteps
from typing_extensions import Annotated, List

from app.services.agent_types.base import join_messages


class NewsAnalystState(MessagesState):
    agent_id: str
    schema: str
    query: str
    next: str
    execution_plan: str
    coordinator_system_prompt: str
    aggregator_system_prompt: str
    reporter_system_prompt: str
    executive_summary: str
    messages: Annotated[List, join_messages]
    remaining_steps: RemainingSteps
