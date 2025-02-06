from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain.tools.tavily_search import TavilySearchResults
import os
from dotenv import load_dotenv

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")

class SearchInput(BaseModel):
    query: str = Field(description="the research query")


class SearchTool(BaseTool):
    name: str = "web_search"
    description: str = "useful to get any information"
    args_schema: Type[BaseModel] = SearchInput
    max_results: int = 10
    callback_handler: bool = None

    def _run(
        self, query: str
    ) -> str:
        tavily_search = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=self.max_results,
            search_depth="advanced"
        )
        results = tavily_search.invoke({"query": query})
        return results

    def __init__(self, callback_handler=None, **data):
        super().__init__(**data)
        self.callback_handler = callback_handler