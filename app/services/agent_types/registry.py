from app.services.agent_types.base import AgentBase


class AgentRegistry:
    def __init__(
        self,
        test_echo_agent: AgentBase,
        quaks_news_analyst_agent: AgentBase,
        quaks_financial_analyst_v1_agent: AgentBase,
    ):
        self.registry = {
            "test_echo": test_echo_agent,
            "quaks_news_analyst": quaks_news_analyst_agent,
            "quaks_financial_analyst_v1": quaks_financial_analyst_v1_agent,
        }

    def get_agent(self, agent_type: str) -> AgentBase:
        return self.registry[agent_type]
