import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

from config import settings

logger = logging.getLogger(__name__)


class PerplexicaSearchTool(BaseTool):
    """Tool for searching the web using Perplexica"""

    name = "perplexica_search"
    description = """
    A tool for searching the web using Perplexica.
    Use this when you need to find up-to-date information, facts, news, or any other information that might be available online.
    Input should be a search query string.
    """

    base_url: str = Field(default=settings.PERPLEXICA_URL)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _arun(self, query: str) -> str:
        """Run the search asynchronously"""
        try:
            logger.info(f"Searching Perplexica for: {query}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Call the Perplexica search API
                response = await client.post(
                    f"{self.base_url}/api/search",
                    json={"query": query, "max_results": 5}
                )
                response.raise_for_status()

                results = response.json()

                if not results or not results.get("results"):
                    return "No search results found."

                # Format the results
                formatted_results = self._format_search_results(results)
                return formatted_results

        except Exception as e:
            logger.error(f"Error searching Perplexica: {str(e)}")
            return f"Error performing search: {str(e)}"

    def _run(self, query: str) -> str:
        """Run the search synchronously"""
        import asyncio

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._arun(query))

    def _format_search_results(self, results: Dict[str, Any]) -> str:
        """Format the search results into a readable string"""
        formatted = "### Search Results\n\n"

        for idx, result in enumerate(results.get("results", []), 1):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            snippet = result.get("snippet", "No snippet available")

            formatted += f"**Result {idx}: {title}**\n"
            formatted += f"URL: {url}\n"
            formatted += f"Summary: {snippet}\n\n"

        return formatted
