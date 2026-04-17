from unittest.mock import MagicMock

from app.interface.mcp.default_tool_registrar import DefaultToolRegistrar


class TestDefaultToolRegistrar:
    def test_registers_tools(self):
        registrar = DefaultToolRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert "get_agent_list" in tool_names
        assert "publish_content_mcp" in tool_names
