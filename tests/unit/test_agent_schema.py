from app.services.agent_types.schema import ExecutionSteps, SolutionPlan


class TestExecutionSteps:
    def test_create_execution_step(self):
        step = ExecutionSteps(
            agent_name="test_agent",
            title="Test Step",
            description="A test step",
        )
        assert step["agent_name"] == "test_agent"
        assert step["title"] == "Test Step"
        assert step["description"] == "A test step"


class TestSolutionPlan:
    def test_create_solution_plan(self):
        plan = SolutionPlan(
            thought="Thinking about the problem",
            title="User wants to do X",
            steps=[
                ExecutionSteps(
                    agent_name="agent1",
                    title="Step 1",
                    description="First step",
                ),
            ],
        )
        assert plan["thought"] == "Thinking about the problem"
        assert plan["title"] == "User wants to do X"
        assert len(plan["steps"]) == 1
        assert plan["steps"][0]["agent_name"] == "agent1"

    def test_empty_steps(self):
        plan = SolutionPlan(
            thought="No steps needed",
            title="Empty plan",
            steps=[],
        )
        assert plan["steps"] == []
