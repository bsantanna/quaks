import json
import re
from datetime import datetime, timedelta

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import Literal

from app.interface.api.messages.schema import MessageRequest
from app.services.agent_types.base import (
    SupervisedWorkflowAgentBase,
    AgentUtils,
)
from app.services.agent_types.quaks.insights.news import (
    NEWS_AGENTS,
    NEWS_AGENT_CONFIGURATION,
)
from app.services.agent_types.quaks.insights.news.prompts import (
    COORDINATOR_SYSTEM_PROMPT,
    AGGREGATOR_SYSTEM_PROMPT,
    REPORTER_SYSTEM_PROMPT,
)
from app.services.agent_types.quaks.insights.news.state import NewsAnalystState
from app.services.markets_news import MarketsNewsService
from app.services.tasks import TaskProgress

EXECUTION_PLAN = (
    "News analysis plan:\n"
    "1. coordinator: Decide whether to proceed with news analysis\n"
    "2. aggregator: Fetch latest news from the last 24 hours and prioritize by economic impact\n"
    "3. reporter: Group articles by topic, write 4-paragraph summaries, and produce the final briefing"
)


class QuaksNewsAnalystAgent(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils, markets_news_service: MarketsNewsService):
        super().__init__(agent_utils)
        self.markets_news_service = markets_news_service

    def create_default_settings(self, agent_id: str, schema: str):
        prompts = {
            "coordinator_system_prompt": COORDINATOR_SYSTEM_PROMPT,
            "aggregator_system_prompt": AGGREGATOR_SYSTEM_PROMPT,
            "reporter_system_prompt": REPORTER_SYSTEM_PROMPT,
        }
        for key, value in prompts.items():
            self.agent_setting_service.create_agent_setting(
                agent_id=agent_id,
                setting_key=key,
                setting_value=value,
                schema=schema,
            )

    def get_workflow_builder(self, agent_id: str):
        workflow_builder = StateGraph(NewsAnalystState)
        workflow_builder.add_edge(START, "coordinator")
        workflow_builder.add_node("coordinator", self.get_coordinator)
        workflow_builder.add_node("aggregator", self.get_aggregator)
        workflow_builder.add_node("reporter", self.get_reporter)
        # Deterministic sequential edges — no supervisor LLM calls needed
        workflow_builder.add_edge("aggregator", "reporter")
        workflow_builder.add_edge("reporter", END)
        return workflow_builder

    def get_input_params(self, message_request: MessageRequest, schema: str) -> dict:
        settings = self.agent_setting_service.get_agent_settings(
            message_request.agent_id, schema
        )
        settings_dict = {
            setting.setting_key: setting.setting_value for setting in settings
        }

        template_vars = {
            "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
            "EXECUTION_PLAN": EXECUTION_PLAN,
            "NEWS_AGENTS": NEWS_AGENTS,
            "NEWS_AGENT_CONFIGURATION": NEWS_AGENT_CONFIGURATION,
        }

        return {
            "agent_id": message_request.agent_id,
            "schema": schema,
            "query": message_request.message_content,
            "execution_plan": EXECUTION_PLAN,
            "coordinator_system_prompt": self.parse_prompt_template(
                settings_dict, "coordinator_system_prompt", template_vars
            ),
            "aggregator_system_prompt": self.parse_prompt_template(
                settings_dict, "aggregator_system_prompt", template_vars
            ),
            "reporter_system_prompt": self.parse_prompt_template(
                settings_dict, "reporter_system_prompt", template_vars
            ),
            "messages": [HumanMessage(content=message_request.message_content)],
        }

    def _build_fetch_news_tool(self):
        markets_news_service = self.markets_news_service

        @tool("fetch_latest_news")
        def fetch_latest_news(
            search_term: str = "",
            size: int = 50,
        ) -> str:
            """Fetch the latest market news articles from the last 24 hours.

            Args:
                search_term: Optional search term to filter news (e.g. sector, company, topic).
                size: Number of articles to fetch (default 50, max 50).

            Returns:
                JSON string with the list of news articles.
            """
            import asyncio

            actual_size = min(size, 50)
            date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            loop = asyncio.new_event_loop()
            try:
                results, _ = loop.run_until_complete(
                    markets_news_service.get_news(
                        index_name="quaks_markets-news_latest",
                        search_term=search_term if search_term else None,
                        date_from=date_from,
                        size=actual_size,
                        include_text_content=True,
                        include_key_ticker=True,
                    )
                )
            finally:
                loop.close()
            articles = []
            for hit in results:
                source = hit["_source"]
                articles.append({
                    "headline": source.get("text_headline", ""),
                    "summary": source.get("text_summary", ""),
                    "content": source.get("text_content", ""),
                    "source": source.get("key_source", ""),
                    "date": source.get("date_reference", ""),
                    "tickers": source.get("key_ticker", []),
                })
            return json.dumps(articles, ensure_ascii=False)

        return fetch_latest_news

    def _invoke_chain(self, agent_id, schema, system_prompt, state):
        """Invoke a simple system+messages chain and return a single AIMessage."""
        chat_model = self.get_chat_model(agent_id, schema)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("placeholder", "{messages}"),
            ]
        )
        chain = prompt | chat_model
        response = chain.invoke({"messages": state["messages"]})
        return response

    def get_coordinator(
        self, state: NewsAnalystState
    ) -> Command[Literal["aggregator", "__end__"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]
        query = state["query"]

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=f"Analyzing query: {query}",
            )
        )

        if query.strip() == "BATCH_ETL":
            self.logger.info(f"Agent[{agent_id}] -> Coordinator -> BATCH_ETL -> aggregator")
            return Command(goto="aggregator")

        # QA mode: answer the user's question directly
        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> QA mode")
        response = self._invoke_chain(
            agent_id, schema, state["coordinator_system_prompt"], state
        )
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=response.content)]},
        )

    def get_aggregator(self, state: NewsAnalystState) -> Command[Literal["reporter"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]
        aggregator_system_prompt = state["aggregator_system_prompt"]

        self.logger.info(f"Agent[{agent_id}] -> Aggregator")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Collecting latest news articles...",
            )
        )

        chat_model = self.get_chat_model(agent_id, schema)
        aggregator = create_react_agent(
            model=chat_model,
            tools=[self._build_fetch_news_tool()],
            prompt=aggregator_system_prompt,
        )
        response = aggregator.invoke(state)

        self.logger.info(f"Agent[{agent_id}] -> Aggregator -> Response complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="News articles collected.",
            )
        )
        return Command(
            update={"messages": response["messages"]},
            goto="reporter",
        )

    @staticmethod
    def _extract_executive_summary(html: str) -> str:
        match = re.search(r"<blockquote>(.*?)</blockquote>", html, re.DOTALL)
        return match.group(1).strip() if match else ""

    def get_reporter(self, state: NewsAnalystState):
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Reporter")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Grouping articles, writing summaries, and producing the final briefing...",
            )
        )

        response = self._invoke_chain(
            agent_id, schema, state["reporter_system_prompt"], state
        )

        report_html = response.content
        executive_summary = self._extract_executive_summary(report_html)

        self.logger.info(f"Agent[{agent_id}] -> Reporter -> Response complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=executive_summary[:200] if executive_summary else report_html[:200],
            )
        )
        return {
            "messages": [AIMessage(content=report_html, name="reporter")],
            "executive_summary": executive_summary,
        }

    def format_response(self, workflow_state: MessagesState) -> (str, dict):
        report_html = workflow_state["messages"][-1].content
        executive_summary = workflow_state.get("executive_summary", "")
        response_data = {
            "executive_summary": executive_summary,
            "report_html": report_html,
            "messages": [
                json.loads(message.model_dump_json())
                for message in workflow_state["messages"]
            ],
        }
        return report_html, response_data

    # --- Abstract method stubs (not used — graph uses deterministic edges) ---

    def get_planner(self, state: NewsAnalystState) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")

    def get_supervisor(self, state: NewsAnalystState) -> Command:
        return Command(goto=END)
