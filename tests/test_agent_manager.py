import pytest
from src.agent_manager import AgentManager
from src.llm import OpenAIProvider, AnthropicProvider
from src.tools.base_tools import WebSearchTool
from smolagents import Tool

class MockTool(Tool):
    name = "mock_tool"
    description = "A mock tool for testing"
    inputs = {
        "input": {
            "type": "string",
            "description": "Test input"
        }
    }
    output_type = "string"

    def forward(self, input: str) -> str:
        return f"Processed: {input}"

class MockLLMProvider:
    def generate_response(self, messages, system_prompt=None, stream=False, **kwargs):
        return "Mock response"

    def get_tool_call(self, messages, available_tools, stop_sequences, **kwargs):
        return None

@pytest.fixture
def mock_llm_provider():
    return MockLLMProvider()

@pytest.fixture
def mock_tool():
    return MockTool()

@pytest.fixture
def agent_manager(mock_llm_provider):
    return AgentManager(llm_provider=mock_llm_provider)

def test_agent_manager_initialization(agent_manager):
    assert agent_manager.llm_provider is not None
    assert len(agent_manager.tools) > 0
    assert agent_manager.max_steps > 0
    assert isinstance(agent_manager.verbose, bool)

def test_add_tool(agent_manager, mock_tool):
    initial_tool_count = len(agent_manager.tools)
    agent_manager.add_tool(mock_tool)
    assert len(agent_manager.tools) == initial_tool_count + 1
    assert any(tool.name == mock_tool.name for tool in agent_manager.tools)

def test_remove_tool(agent_manager, mock_tool):
    agent_manager.add_tool(mock_tool)
    initial_tool_count = len(agent_manager.tools)
    agent_manager.remove_tool(mock_tool.name)
    assert len(agent_manager.tools) == initial_tool_count - 1
    assert not any(tool.name == mock_tool.name for tool in agent_manager.tools)

def test_get_available_tools(agent_manager, mock_tool):
    agent_manager.add_tool(mock_tool)
    tools_info = agent_manager.get_available_tools()
    assert isinstance(tools_info, list)
    assert len(tools_info) > 0
    
    mock_tool_info = next((tool for tool in tools_info if tool['name'] == mock_tool.name), None)
    assert mock_tool_info is not None
    assert mock_tool_info['description'] == mock_tool.description
    assert mock_tool_info['inputs'] == mock_tool.inputs
    assert mock_tool_info['output_type'] == mock_tool.output_type

def test_process_request(agent_manager):
    response = agent_manager.process_request("Test request")
    assert response is not None

def test_process_request_with_stream(agent_manager):
    response = agent_manager.process_request("Test request", stream=True)
    assert response is not None

def test_update_configuration(agent_manager, mock_llm_provider):
    new_max_steps = 20
    new_verbose = not agent_manager.verbose
    
    agent_manager.update_configuration(
        llm_provider=mock_llm_provider,
        max_steps=new_max_steps,
        verbose=new_verbose
    )
    
    assert agent_manager.llm_provider == mock_llm_provider
    assert agent_manager.max_steps == new_max_steps
    assert agent_manager.verbose == new_verbose

def test_get_agent_status(agent_manager):
    status = agent_manager.get_agent_status()
    assert isinstance(status, dict)
    assert 'llm_provider' in status
    assert 'num_tools' in status
    assert 'max_steps' in status
    assert 'verbose' in status
    assert status['num_tools'] == len(agent_manager.tools)
    assert status['max_steps'] == agent_manager.max_steps
    assert status['verbose'] == agent_manager.verbose

def test_error_handling(agent_manager):
    # Test with invalid request
    response = agent_manager.process_request(None)
    assert isinstance(response, dict)
    assert response.get('error') is True
    assert 'message' in response 