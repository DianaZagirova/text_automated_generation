from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Source:
    url: str
    title: str
    preview_text: str
    screenshot_path: Optional[str] = None

@dataclass
class Report:
    content: str  # Original markdown content
    formatted_content: str  # HTML-formatted content for display
    sources: List[Source]
    research_plan: List[str]
