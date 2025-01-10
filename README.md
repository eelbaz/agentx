# AgentX Assistant

AgentX Assistant is a powerful AI agent framework built on top of the smolagents paradigm, designed to create and manage intelligent agents that can perform complex tasks using Python code and a variety of tools.

## Features

- 🤖 Multi-provider LLM support (OpenAI, Anthropic, DeepSeek, Ollama)
- 🛠️ Extensible tool system for agent capabilities
- 🌐 Web-based user interface for agent interaction
- ⚡ Real-time streaming of agent responses
- 🔄 Built-in error handling and recovery
- 🔒 Secure package management and execution

## Installation

1. Clone the repository:
```bash
git clone https://github.com/eelbaz/agentx.git
cd agentx
```

2. Create and activate a virtual environment:
```bash
# On Unix/macOS
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

2. Required API keys:
- `OPENAI_API_KEY`: For OpenAI models
- `ANTHROPIC_API_KEY`: For Anthropic models
- `HF_API_TOKEN`: For Hugging Face models
- `DEEPSEEK_API_KEY`: For DeepSeek models

Optional API keys:
- Twitter API keys (for Twitter search functionality)
- E2B API key (for secure code execution)

## Running the Application

Start the FastAPI application:
```bash
uvicorn src.app:app --reload
```

The application will be available at `http://localhost:8000`.

## Available Tools

### Core Tools
- 🔍 Web Search Tool (DuckDuckGo integration)
- 🌐 Web Scrape Tool
- 💻 System Command Tool
- 📁 File System Tool
- 🐦 Twitter Search Tool
- ℹ️ System Info Tool

## Usage

1. Select your preferred LLM provider (OpenAI, Anthropic, DeepSeek, or Ollama)
2. Choose a model from the available options
3. Type your request in the chat input
4. The agent will:
   - Analyze your request
   - Create an execution plan
   - Use appropriate tools to fulfill the request
   - Stream the response back to you

## Development

### Project Structure
```
agentx/
├── src/
│   ├── tools/
│   │   └── base_tools.py
│   ├── agent_manager.py
│   ├── llm.py
│   └── app.py
├── tests/
├── requirements.txt
└── README.md
```

### Adding New Tools

1. Create a new tool class inheriting from `Tool`:
```python
from smolagents import Tool

class YourNewTool(Tool):
    name = "your_tool_name"
    description = "Description of what your tool does"
    inputs = {
        "param1": {
            "type": "string",
            "description": "Description of param1"
        }
    }
    output_type = "string"

    def forward(self, param1: str) -> str:
        # Implement your tool logic here
        pass
```

2. Register the tool with the AgentManager:
```python
agent_manager.add_tool(YourNewTool())
```

### Security Considerations

- Environment variables are used for all sensitive information
- Package imports are restricted to a safe allowlist
- Code execution is sandboxed (when using E2B)
- All tool executions are logged and monitored

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 