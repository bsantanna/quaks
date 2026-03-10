import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.constants import START, END
from langgraph.graph import StateGraph
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
    HEADLINES_CREATOR_SYSTEM_PROMPT,
    NEWS_WRITER_SYSTEM_PROMPT,
    EDITOR_SYSTEM_PROMPT,
)
from app.services.agent_types.quaks.insights.news.schema import CoordinatorRouter
from app.services.agent_types.quaks.insights.news.state import NewsAnalystState
from app.services.markets_news import MarketsNewsService
from app.services.tasks import TaskProgress

EXECUTION_PLAN = (
    "News analysis plan:\n"
    "1. aggregator: Fetch latest news from the last 24 hours\n"
    "2. headlines_creator: Group articles by topic and create headlines\n"
    "3. news_writer: Write 3-paragraph summaries per topic\n"
    "4. editor: Format the final investor briefing report"
)


class QuaksNewsAnalystAgent(SupervisedWorkflowAgentBase):
    def __init__(self, agent_utils: AgentUtils, markets_news_service: MarketsNewsService):
        super().__init__(agent_utils)
        self.markets_news_service = markets_news_service

    def create_default_settings(self, agent_id: str, schema: str):
        prompts = {
            "coordinator_system_prompt": COORDINATOR_SYSTEM_PROMPT,
            "aggregator_system_prompt": AGGREGATOR_SYSTEM_PROMPT,
            "headlines_creator_system_prompt": HEADLINES_CREATOR_SYSTEM_PROMPT,
            "news_writer_system_prompt": NEWS_WRITER_SYSTEM_PROMPT,
            "editor_system_prompt": EDITOR_SYSTEM_PROMPT,
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
        workflow_builder.add_node("headlines_creator", self.get_headlines_creator)
        workflow_builder.add_node("news_writer", self.get_news_writer)
        workflow_builder.add_node("editor", self.get_editor)
        # Deterministic sequential edges — no supervisor LLM calls needed
        workflow_builder.add_edge("aggregator", "headlines_creator")
        workflow_builder.add_edge("headlines_creator", "news_writer")
        workflow_builder.add_edge("news_writer", "editor")
        workflow_builder.add_edge("editor", END)
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
            "headlines_creator_system_prompt": self.parse_prompt_template(
                settings_dict, "headlines_creator_system_prompt", template_vars
            ),
            "news_writer_system_prompt": self.parse_prompt_template(
                settings_dict, "news_writer_system_prompt", template_vars
            ),
            "editor_system_prompt": self.parse_prompt_template(
                settings_dict, "editor_system_prompt", template_vars
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
            """Fetch the latest market news articles from Elasticsearch.

            Args:
                search_term: Optional search term to filter news (e.g. sector, company, topic).
                size: Number of articles to fetch (default 50, max 50).

            Returns:
                JSON string with the list of news articles.
            """
            import asyncio

            actual_size = min(size, 50)
            results, _ = asyncio.get_event_loop().run_until_complete(
                markets_news_service.get_news(
                    index_name="quaks_markets-news_latest",
                    search_term=search_term if search_term else None,
                    size=actual_size,
                    include_text_content=True,
                    include_key_ticker=True,
                )
            )
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
        coordinator_system_prompt = state["coordinator_system_prompt"]

        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Query -> {query}")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=f"Analyzing query: {query}",
            )
        )
        chat_model = self.get_chat_model(agent_id, schema)
        chat_model_with_structured_output = chat_model.with_structured_output(
            CoordinatorRouter
        )
        response = self.get_coordinator_chain(
            chat_model_with_structured_output, coordinator_system_prompt
        ).invoke({"query": query})
        self.logger.info(f"Agent[{agent_id}] -> Coordinator -> Response -> {response}")

        if response["next"] == END:
            return Command(
                goto=response["next"],
                update={"messages": [AIMessage(content=response["generated"])]},
            )
        else:
            return Command(goto="aggregator")

    def get_aggregator(self, state: NewsAnalystState) -> Command[Literal["headlines_creator"]]:
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
            goto="headlines_creator",
        )

    def get_headlines_creator(self, state: NewsAnalystState) -> Command[Literal["news_writer"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Headlines Creator")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Grouping articles and creating topic headlines...",
            )
        )

        response = self._invoke_chain(
            agent_id, schema, state["headlines_creator_system_prompt"], state
        )

        self.logger.info(f"Agent[{agent_id}] -> Headlines Creator -> Response complete")
        return Command(
            update={"messages": [AIMessage(content=response.content, name="headlines_creator")]},
            goto="news_writer",
        )

    def get_news_writer(self, state: NewsAnalystState) -> Command[Literal["editor"]]:
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> News Writer")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Writing topic summaries...",
            )
        )

        response = self._invoke_chain(
            agent_id, schema, state["news_writer_system_prompt"], state
        )

        self.logger.info(f"Agent[{agent_id}] -> News Writer -> Response complete")
        return Command(
            update={"messages": [AIMessage(content=response.content, name="news_writer")]},
            goto="editor",
        )

    def get_editor(self, state: NewsAnalystState):
        agent_id = state["agent_id"]
        schema = state["schema"]

        self.logger.info(f"Agent[{agent_id}] -> Editor")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content="Formatting final investor briefing...",
            )
        )

        response = self._invoke_chain(
            agent_id, schema, state["editor_system_prompt"], state
        )

        self.logger.info(f"Agent[{agent_id}] -> Editor -> Response complete")
        self.task_notification_service.publish_update(
            task_progress=TaskProgress(
                agent_id=agent_id,
                status="in_progress",
                message_content=response.content[:200],
            )
        )
        return {"messages": [AIMessage(content=response.content, name="editor")]}

    # --- Abstract method stubs (not used — graph uses deterministic edges) ---

    def get_planner(self, state: NewsAnalystState) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")

    def get_supervisor(self, state: NewsAnalystState) -> Command:
        return Command(goto=END)

    def get_reporter(self, state: NewsAnalystState) -> Command[Literal["supervisor"]]:
        return Command(goto="supervisor")
