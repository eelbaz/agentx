import pytest
import os
from src.llm import OpenAIProvider, AnthropicProvider
from smolagents import Tool

class TestTool(Tool):
    name = "test_tool"
    description = "A test tool"
    inputs = {
        "input": {
            "type": "string",
            "description": "Test input"
        }
    }
    output_type = "string"

    def forward(self, input: str) -> str:
        return f"Test output: {input}"

@pytest.fixture
def openai_provider():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    return OpenAIProvider()

@pytest.fixture
def anthropic_provider():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("Anthropic API key not available")
    return AnthropicProvider()

@pytest.fixture
def test_tool():
    return TestTool()

@pytest.fixture
def test_messages():
    return [
        {"role": "user", "content": "Hello, how are you?"}
    ]

def test_openai_generate_response(openai_provider, test_messages):
    response = openai_provider.generate_response(test_messages)
    assert isinstance(response, str)
    assert len(response) > 0

def test_openai_generate_response_with_system_prompt(openai_provider, test_messages):
    system_prompt = "You are a helpful assistant."
    response = openai_provider.generate_response(test_messages, system_prompt=system_prompt)
    assert isinstance(response, str)
    assert len(response) > 0

def test_openai_generate_response_streaming(openai_provider, test_messages):
    response = openai_provider.generate_response(test_messages, stream=True)
    chunks = list(response)
    assert len(chunks) > 0

def test_openai_tool_call(openai_provider, test_messages, test_tool):
    tool_call = openai_provider.get_tool_call(
        test_messages,
        [test_tool],
        ["stop"]
    )
    assert tool_call is None or isinstance(tool_call, dict)

def test_anthropic_generate_response(anthropic_provider, test_messages):
    response = anthropic_provider.generate_response(test_messages)
    assert isinstance(response, str)
    assert len(response) > 0

def test_anthropic_generate_response_with_system_prompt(anthropic_provider, test_messages):
    system_prompt = "You are a helpful assistant."
    response = anthropic_provider.generate_response(test_messages, system_prompt=system_prompt)
    assert isinstance(response, str)
    assert len(response) > 0

def test_anthropic_generate_response_streaming(anthropic_provider, test_messages):
    response = anthropic_provider.generate_response(test_messages, stream=True)
    chunks = list(response)
    assert len(chunks) > 0

def test_anthropic_tool_call(anthropic_provider, test_messages, test_tool):
    tool_call = anthropic_provider.get_tool_call(
        test_messages,
        [test_tool],
        ["stop"]
    )
    assert tool_call is None or isinstance(tool_call, dict)

def test_openai_provider_initialization():
    with pytest.raises(Exception):
        # Should raise an exception when API key is not set
        os.environ.pop("OPENAI_API_KEY", None)
        OpenAIProvider()

def test_anthropic_provider_initialization():
    with pytest.raises(Exception):
        # Should raise an exception when API key is not set
        os.environ.pop("ANTHROPIC_API_KEY", None)
        AnthropicProvider()

def test_openai_provider_invalid_model():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    
    with pytest.raises(Exception):
        provider = OpenAIProvider(model_name="invalid-model")
        provider.generate_response([{"role": "user", "content": "test"}])

def test_anthropic_provider_invalid_model():
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("Anthropic API key not available")
    
    with pytest.raises(Exception):
        provider = AnthropicProvider(model_name="invalid-model")
        provider.generate_response([{"role": "user", "content": "test"}]) 