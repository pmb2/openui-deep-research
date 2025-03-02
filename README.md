# Custom Open Deep Research Agent

A custom open-source deep research agent that integrates:

- Groq's DeepSeek-R1-Distill-Llama-70B for reasoning (with Ollama fallback)
- Perplexica for advanced search capabilities
- Open WebUI for a user-friendly interface
- Support for multiple asynchronous chat sessions

## Features

- **Advanced AI Research**: Leverage powerful language models for in-depth research
- **Multiple Search Sources**: Use Perplexica to search across various web sources
- **Asynchronous Chats**: Run multiple research sessions simultaneously
- **Fallback Options**: Seamlessly switch between cloud and local models
- **Docker Deployment**: Simple setup and deployment using Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Groq API key (sign up at [groq.com](https://groq.com))

### Installation

1. Clone this repository:

```

git clone https://github.com/pmb2/openui-deep-research.git
cd openui-deep-research

```

2. Run the setup script:

```

./scripts/install_dependencies.sh

```

3. Edit the `.env` file and add your Groq API key.

4. Start the services:

```

./scripts/start.sh

```

5. Access the web interface at: http://localhost:3001

## Usage

1. Open the web interface and create a new Research Chat
2. Ask your research question
3. The agent will search for information and provide a comprehensive answer
4. You can start multiple research chats that will run asynchronously

## Architecture

- **Backend**: FastAPI application that orchestrates the research process
- **LLM Providers**: Groq Cloud (primary) and Ollama (fallback)
- **Search Engine**: Perplexica for web searching
- **Frontend**: Open WebUI with custom plugins for research chat

## Configuration

You can configure the agent by editing the `.env` file:

- `GROQ_API_KEY`: Your Groq API key
- `GROQ_MODEL`: The model to use on Groq (default: deepseek-r1-distill-llama-70b)
- `USE_OLLAMA_FALLBACK`: Whether to use Ollama as a fallback (true/false)
- `OLLAMA_MODEL`: The model to use with Ollama (default: deepseek-r1-distill-llama-70b)
- `SESSION_TIMEOUT_MINUTES`: Inactive session timeout (default: 60)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LangChain's Open Deep Research](https://github.com/langchain-ai/open_deep_research)
- [ItzCrazyKns's Perplexica](https://github.com/ItzCrazyKns/Perplexica)
- [Open WebUI](https://github.com/open-webui/open-webui)
- [Groq](https://groq.com/)
- [Ollama](https://ollama.com/)
