import logging
from typing import Any, Dict, Optional

from langchain_groq import ChatGroq
from langchain.schema import LLMResult
from langchain.callbacks.base import BaseCallbackHandler

from config import settings

logger = logging.getLogger(__name__)


def get_groq_llm(model: str = None) -> ChatGroq:
    """
    Initialize and return a Groq LLM instance

    Args:
        model: The model to use (defaults to the one in settings)

    Returns:
        A configured ChatGroq instance
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set")

    model_name = model or settings.GROQ_MODEL

    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=model_name,
        temperature=0.2,  # Lower temperature for more deterministic responses
        streaming=True,
        max_tokens=8192,
    )


def get_ollama_llm(model: str = None) -> Any:
    """
    Initialize and return an Ollama LLM instance

    Args:
        model: The model to use (defaults to the one in settings)

    Returns:
        A configured Ollama LLM instance
    """
    from langchain_community.llms import Ollama

    model_name = model or settings.OLLAMA_MODEL

    return Ollama(
        model=model_name,
        base_url=settings.OLLAMA_HOST,
        temperature=0.2,
        streaming=True,
    )
