import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
import json

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.tools import BaseTool
from langchain.callbacks.base import BaseCallbackHandler

from agent.models import get_groq_llm, get_ollama_llm
from agent.search import PerplexicaSearchTool
from config import settings

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses"""

    def __init__(self, streaming_callback: Callable[[str, Dict[str, Any]], None]):
        self.streaming_callback = streaming_callback
        self.tokens = []

    def on_llm_new_token(self, token: str, **kwargs):
        self.tokens.append(token)
        self.streaming_callback(token, {})

    def on_tool_start(self, tool: str, input_str: str, **kwargs):
        tool_info = {
            "event": "tool_start",
            "tool": tool,
            "input": input_str
        }
        self.streaming_callback("", tool_info)

    def on_tool_end(self, output: str, **kwargs):
        tool_info = {
            "event": "tool_end",
            "output": output
        }
        self.streaming_callback("", tool_info)


class ResearchAgent:
    """The main research agent that orchestrates the research process"""

    def __init__(self, session_id: str, streaming_callback: Optional[Callable] = None):
        self.session_id = session_id
        self.streaming_callback = streaming_callback or (lambda x, y: None)
        self.callbacks = [StreamingCallbackHandler(self.streaming_callback)]
        self.tools = self._get_tools()
        self.agent_executor = self._create_agent_executor()
        self.conversation_history = []
        self.use_groq = True  # Start with Groq by default

    def _get_tools(self) -> List[BaseTool]:
        """Initialize and return the tools for the agent"""
        search_tool = PerplexicaSearchTool(base_url=settings.PERPLEXICA_URL)
        return [search_tool]

    def _create_agent_executor(self) -> AgentExecutor:
        """Create and return the agent executor"""
        try:
            # First try with Groq
            llm = get_groq_llm(model=settings.GROQ_MODEL)
            self.use_groq = True
        except Exception as e:
            logger.warning(f"Failed to initialize Groq LLM: {str(e)}. Falling back to Ollama.")
            if not settings.USE_OLLAMA_FALLBACK:
                raise
            llm = get_ollama_llm(model=settings.OLLAMA_MODEL)
            self.use_groq = False

        # System prompt for the research agent
        system_prompt = """You are an advanced AI research assistant designed to help users with in-depth research.
        Use the provided tools to search for information and synthesize detailed, accurate responses.
        Always cite your sources and provide comprehensive answers. If you don't know something, say so rather than making up information.
        Think step by step and be thorough in your research process."""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content="{input}"),
        ])

        # Create the agent
        agent = create_openai_tools_agent(llm, self.tools, prompt)

        # Create the agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            handle_parsing_errors=True,
            max_iterations=10,
            verbose=True,
        )

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and return the results"""
        start_time = time.time()

        try:
            self.streaming_callback("", {"event": "research_start", "query": query})

            # Add query to conversation history
            self.conversation_history.append({"role": "user", "content": query})

            # Run the agent
            result = await asyncio.to_thread(
                self.agent_executor.invoke,
                {"input": query},
                {"callbacks": self.callbacks}
            )

            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": result["output"]})

            process_time = time.time() - start_time

            response = {
                "success": True,
                "result": result["output"],
                "process_time": process_time,
                "model": settings.GROQ_MODEL if self.use_groq else settings.OLLAMA_MODEL,
                "provider": "Groq" if self.use_groq else "Ollama",
            }

            self.streaming_callback("", {"event": "research_complete", "response": response})
            return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            error_response = {
                "success": False,
                "error": str(e),
                "process_time": time.time() - start_time,
            }
            self.streaming_callback("", {"event": "research_error", "error": error_response})
            return error_response

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Return the conversation history"""
        return self.conversation_history
