import os
from uuid import uuid4

import scenario
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    yield TestClient(app)


scenario.configure(default_model="openai/gpt-4.1-2025-04-14")


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_news_analyst_daily_briefing(client):
    class NewsAnalystAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return news_analyst_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: Quaks News Analyst daily briefing",
        description="Generate a investor briefing from market news available",
        agents=[
            NewsAnalystAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not ask follow-up questions.",
                    "Agent should generate a report formatted as HTML using h1, h2, p, blockquote, and hr tags.",
                    "Report should contain an executive summary inside a blockquote tag.",
                    "Report should contain multiple topic sections, each with a headline and paragraphs.",
                    "Report should use simple, plain language suitable for non-expert investors.",
                    "Report should NOT contain garbled text, LaTeX, or broken Markdown formatting.",
                ],
            ),
        ],
        script=[
            scenario.user("Give market news briefing from news you have available."),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_news_analyst_response_data_structure(client):
    class NewsAnalystAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return news_analyst_agent_full_response(client, user_message)

    result = await scenario.run(
        name="Simulation: Quaks News Analyst response structure",
        description="Verify the JSON response contains executive_summary and report_html fields",
        agents=[
            NewsAnalystAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not ask follow-up questions.",
                    "Response should contain an executive_summary field with a non-empty string.",
                    "Response should contain a report_html field with HTML content.",
                    "The executive_summary should be a concise one-sentence summary of market themes.",
                ],
            ),
        ],
        script=[
            scenario.user("Give me today's market news briefing."),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@pytest.mark.agent_test
@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=os.getenv("BUILD_WORKFLOW") == "True", reason="Skip Github CI."
)
async def test_news_analyst_off_topic_rejection(client):
    class NewsAnalystAgent(scenario.AgentAdapter):
        async def call(self, input: scenario.AgentInput) -> scenario.AgentReturnTypes:
            user_message = input.last_new_user_message_str()
            return news_analyst_agent(client, user_message)

    result = await scenario.run(
        name="Simulation: Quaks News Analyst off-topic rejection",
        description="Verify the agent rejects off-topic requests gracefully",
        agents=[
            NewsAnalystAgent(),
            scenario.UserSimulatorAgent(),
            scenario.JudgeAgent(
                temperature=1.0,
                criteria=[
                    "Agent should not generate a full news briefing report.",
                    "Agent should politely explain that it can only help with market news analysis.",
                    "Response should be brief and not contain HTML report structure.",
                ],
            ),
        ],
        script=[
            scenario.user("Write me a poem about cats."),
            scenario.agent(),
            scenario.judge(),
        ],
    )

    assert result.success


@scenario.cache()
def news_analyst_agent(client, message_content) -> scenario.AgentReturnTypes:
    agent_id = _setup_agent(client)

    response = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )

    return response.json()["message_content"]


@scenario.cache()
def news_analyst_agent_full_response(
    client, message_content
) -> scenario.AgentReturnTypes:
    agent_id = _setup_agent(client)

    response = client.post(
        "/messages/post",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "message_role": "human",
            "message_content": message_content,
            "agent_id": agent_id,
        },
    )

    response_data = response.json().get("response_data", {})
    executive_summary = response_data.get("executive_summary", "")
    report_html = response_data.get("report_html", "")

    return f"executive_summary: {executive_summary}\n\n" f"report_html: {report_html}"


def _setup_agent(client):
    # create integration
    response = client.post(
        url="/integrations/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "api_endpoint": "https://api.x.ai/v1/",
            "api_key": os.environ["XAI_API_KEY"],
            "integration_type": "xai_api_v1",
        },
    )
    integration_id = response.json()["id"]

    # create llm
    response_2 = client.post(
        url="/llms/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "integration_id": integration_id,
            "language_model_tag": "grok-4-1-fast-non-reasoning",
        },
    )
    language_model_id = response_2.json()["id"]

    # create agent
    response_3 = client.post(
        url="/agents/create",
        headers={"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"},
        json={
            "language_model_id": language_model_id,
            "agent_type": "quaks_news_analyst",
            "agent_name": f"agent-{uuid4()}",
        },
    )

    return response_3.json()["id"]
