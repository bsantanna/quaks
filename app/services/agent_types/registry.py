from app.services.agent_types.base import AgentBase


class AgentRegistry:
    def __init__(
        self,
        test_echo_agent: AgentBase,
        quaks_news_analyst_agent: AgentBase,
    ):
        self.registry = {
            "test_echo": test_echo_agent,
            "quaks_news_analyst": quaks_news_analyst_agent,
        }

    def get_agent(self, agent_type: str) -> AgentBase:
        return self.registry[agent_type]
