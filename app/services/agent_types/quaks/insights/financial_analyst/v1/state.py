from langgraph.graph import MessagesState
from langgraph.managed import RemainingSteps
from typing_extensions import Annotated, List

from app.services.agent_types.base import join_messages


class FinancialAnalystState(MessagesState):
    agent_id: str
    schema: str
    query: str
    tickers: List[str]
    next: str
    execution_plan: str
    coordinator_system_prompt: str
    data_collector_system_prompt: str
    fundamental_analyst_system_prompt: str
    technical_analyst_system_prompt: str
    consensus_reporter_system_prompt: str
    fundamental_recommendation: str
    technical_recommendation: str
    consensus_verdict: str
    executive_summary: str
    allocation_weights: str
    portfolio_xray_html: str
    messages: Annotated[List, join_messages]
    remaining_steps: RemainingSteps
