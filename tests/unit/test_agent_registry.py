from unittest.mock import MagicMock
import pytest
from app.services.agent_types.registry import AgentRegistry
from app.services.agent_types.base import AgentBase

def test_agent_registry():
    mock_echo = MagicMock(spec=AgentBase)
    mock_news = MagicMock(spec=AgentBase)
    mock_financial = MagicMock(spec=AgentBase)
    
    registry = AgentRegistry(
        test_echo_agent=mock_echo,
        quaks_news_analyst_agent=mock_news,
        quaks_financial_analyst_v1_agent=mock_financial
    )
    
    assert registry.get_agent("test_echo") == mock_echo
    assert registry.get_agent("quaks_news_analyst") == mock_news
    assert registry.get_agent("quaks_financial_analyst_v1") == mock_financial
    
    with pytest.raises(KeyError):
        registry.get_agent("invalid")
