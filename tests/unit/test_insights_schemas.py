from app.services.agent_types.quaks.insights.financial_analyst.v1.schema import CoordinatorRouter as FACoordinatorRouter
from app.services.agent_types.quaks.insights.news.schema import CoordinatorRouter as NewsCoordinatorRouter


class TestFinancialAnalystSchema:
    def test_coordinator_router_data_collector(self):
        router: FACoordinatorRouter = {"next": "data_collector", "generated": ""}
        assert router["next"] == "data_collector"
        assert router["generated"] == ""

    def test_coordinator_router_end(self):
        router: FACoordinatorRouter = {"next": "__end__", "generated": "Final answer"}
        assert router["next"] == "__end__"
        assert router["generated"] == "Final answer"


class TestNewsSchema:
    def test_coordinator_router_aggregator(self):
        router: NewsCoordinatorRouter = {"next": "aggregator", "generated": ""}
        assert router["next"] == "aggregator"
        assert router["generated"] == ""

    def test_coordinator_router_end(self):
        router: NewsCoordinatorRouter = {"next": "__end__", "generated": "Report text"}
        assert router["next"] == "__end__"
        assert router["generated"] == "Report text"
