# AgentX Assistant

AgentX Assistant is a powerful AI agent framework built on top of the smolagents paradigm, designed to create and manage intelligent agents that can perform complex tasks using Python code and a variety of tools.

## Features

- Multi-provider LLM support (OpenAI, Anthropic)
- Extensible tool system for agent capabilities
- Web-based user interface for agent interaction
- Real-time streaming of agent responses
- Built-in error handling and recovery
- Support for media generation and manipulation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agentx.git
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

1. Create a `.env` file in the project root with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_twitter_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_token_secret
```

## Running the Application

Start the Streamlit application:
```bash
streamlit run src/app.py
```

The application will be available at `http://localhost:8501`.

## Available Tools

### Base Tools
- Web Search Tool (DuckDuckGo integration)
- Web Scrape Tool
- System Command Tool
- File System Tool
- Twitter Search Tool
- System Info Tool

### Media Tools
- Image Generation Tool
- Video Generation Tool

## Usage

1. Select your preferred LLM provider in the sidebar (OpenAI or Anthropic)
2. Type your request in the chat input
3. The agent will:
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
│   │   ├── base_tools.py
│   │   └── media_tools.py
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