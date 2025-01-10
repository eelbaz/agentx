# 🤖 AgentX

AgentX is your AI-powered coding companion that thinks, codes, and solves problems alongside you. Built on the smolagents framework, it combines the power of multiple LLMs with a suite of specialized tools to help you tackle complex programming tasks.

![AgentX Demo](docs/demo.gif)

## ✨ What Makes AgentX Special

- **Multi-Brain Intelligence**: Switch between different LLM providers (OpenAI, Anthropic, DeepSeek, Ollama) to leverage their unique strengths
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

# Configure your keys
cp .env.example .env     # Then edit .env with your API keys

# Launch!
uvicorn src.app:app --reload
```

Then open http://localhost:8000 in your browser and start chatting with your new coding companion!

## 🔑 API Keys

You'll need at least one of these to get started:
- OpenAI API key (recommended)
- Anthropic API key
- HuggingFace API token
- DeepSeek API key

Optional but enhances capabilities:
- Twitter API keys (for research)
- E2B API key (for secure code execution)

## 🛠️ Core Tools

AgentX comes equipped with:

| Tool | Description |
|------|-------------|
| 🔍 Web Search | Research using DuckDuckGo |
| 🌐 Web Scraper | Extract data from websites |
| 💻 System Commander | Execute system commands safely |
| 📁 File Manager | Handle file operations |
| 🐦 Twitter Explorer | Search Twitter data |
| ℹ️ System Inspector | Get system information |

## 💡 Example Uses

```python
# Ask AgentX to help with coding tasks
"Help me write a Python script to batch resize images in a folder"

# Research and summarize
"Find and summarize recent articles about Rust vs Go performance"

# System tasks
"Help me set up a PostgreSQL database with the right configuration for my Django app"
```

## 🔒 Security

AgentX takes security seriously:
- All code execution is sandboxed
- Package imports are strictly controlled
- Environment variables for sensitive data
- Comprehensive logging and monitoring

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

MIT License - feel free to use in your own projects!

## 🙋‍♂️ Need Help?

- 📖 [Documentation](docs/README.md)
- 🐛 [Issue Tracker](https://github.com/eelbaz/agentx/issues)
- 💬 [Discussions](https://github.com/eelbaz/agentx/discussions)

---

<p align="center">
  Made with ❤️ by the AgentX Team
</p> 