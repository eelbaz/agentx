# 🤖 AgentX

AgentX is your AI-powered coding companion that thinks, codes, and solves problems alongside you. Built on the [smolagents](https://huggingface.co/docs/smolagents) framework by the HuggingFace team, with a beautiful interface powered by [OpenWebUI](https://github.com/open-webui/open-webui), it combines the power of multiple LLMs with a suite of specialized tools to help you tackle complex programming tasks.

![AgentX Demo](docs/demo.gif)

## ✨ What Makes AgentX Special

- **Multi-Brain Intelligence**: Switch between different LLM providers to leverage their unique strengths:
  - 🌐 **OpenAI**: State-of-the-art models like GPT-4
  - 🧠 **Anthropic**: Advanced reasoning with Claude
  - 🔒 **Ollama**: Air-gapped, private deployment of open-source models
  - 💻 **DeepSeek**: Specialized coding assistance
- **Real Coding Partner**: Not just suggestions - AgentX writes, tests, and fixes code in real-time
- **Tool-Powered**: Equipped with web search, system commands, file operations, and more
- **Security First**: Sandboxed execution environment with strict package controls
- **Beautiful UI**: Clean, responsive interface with real-time streaming responses

## 🚀 Quick Start

```bash
# Clone and enter the project
git clone https://github.com/eelbaz/agentx.git
cd agentx

# Set up environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# For air-gapped deployment with Ollama:
# 1. Install Ollama from https://ollama.ai
# 2. Pull your preferred models:
ollama pull qwen2.5-plus    # or any other model
# 3. Start Ollama server:
ollama serve

# For cloud providers:
cp .env.example .env     # Then edit .env with your API keys

# Launch!
uvicorn src.app:app --reload
```

Then open http://localhost:8000 in your browser and start chatting with your new coding companion!

## 🔑 LLM Providers

AgentX supports multiple LLM providers to suit your needs:

### 🔒 Ollama (Air-Gapped)
- Run completely offline with open-source models
- No API keys needed
- Perfect for private, secure environments
- Supports models like Qwen, Llama, CodeLlama, and more
- Easy local deployment and model management

### 🌐 Cloud Providers (API Key Required)
- **OpenAI**: GPT-4 and GPT-3.5 models (recommended for best performance)
- **Anthropic**: Claude models for advanced reasoning
- **DeepSeek**: Specialized coding models

## 🔑 API Keys

Only needed for cloud providers (not required for Ollama):
- OpenAI API key
- Anthropic API key
- DeepSeek API key

Optional but enhances capabilities:
- Twitter API keys (for research)
- E2B API key (for secure code execution)

## 🛠️ Core Tools

AgentX comes equipped with a powerful set of default tools, and you can easily extend it with your own:

| Tool | Description |
|------|-------------|
| 🔍 Web Search | Research using DuckDuckGo |
| 🌐 Web Scraper | Extract data from websites |
| 💻 System Commander | Execute system commands safely |
| 📁 File Manager | Handle file operations |
| 🐦 Twitter Explorer | Search Twitter data |
| ℹ️ System Inspector | Get system information |

### 🔧 Adding Custom Tools

Extend AgentX with your own tools by implementing the `Tool` class from smolagents:

```python
from smolagents import Tool

class MyCustomTool(Tool):
    name = "my_custom_tool"
    description = "Description of what your tool does"
    inputs = {
        "param1": {"type": "string", "description": "Parameter description"},
        # Add more parameters as needed
    }
    output_type = "string"  # or any other type

    def forward(self, **inputs):
        # Implement your tool's logic here
        return result
```

Then add your tool to the agent:

```python
from agentx import AgentManager
from my_tools import MyCustomTool

agent = AgentManager(
    additional_tools=[MyCustomTool()]
)
```

## 💡 Example Uses

```python
# Ask AgentX to help with coding tasks
"Help me write a Python script to batch resize images in a folder"

# Research and summarize
"Find and summarize recent articles about Rust vs Go performance"

# System tasks
"Help me set up a PostgreSQL database with the right configuration for my Django app"
```

## 🔒 Security & Privacy

AgentX takes security and privacy seriously:

### Air-Gapped Deployment
- Run completely offline using Ollama provider
- No data leaves your network
- Full control over model selection and updates

### Sandboxed Execution
- All code execution is isolated and controlled
- Package imports are strictly controlled
- Environment variables for sensitive data
- Comprehensive logging and monitoring

### Data Privacy
- Choose between cloud providers or local deployment
- No data retention when using Ollama
- Configurable logging levels
- Strict access controls

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

MIT License - feel free to use in your own projects!

## 🙋 Acknowledgments

AgentX is built on the shoulders of giants:

- [smolagents](https://huggingface.co/docs/smolagents) by HuggingFace - The powerful agent framework that makes AgentX possible
- [OpenWebUI](https://github.com/open-webui/open-webui) - The beautiful and responsive interface
- [Ollama](https://ollama.ai) - Local model deployment and management
- All our amazing contributors and the open-source community

## 🙋‍♂️ Need Help?

- 📖 [Documentation](docs/README.md)
- 🐛 [Issue Tracker](https://github.com/eelbaz/agentx/issues)
- 💬 [Discussions](https://github.com/eelbaz/agentx/discussions)

---

<p align="center">
  Made with ❤️ by the AgentX Team
</p> 