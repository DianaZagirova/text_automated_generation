import os
import base64
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.tavily_search import TavilySearchResults
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain.callbacks import StreamlitCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
import streamlit as st
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any, List, Dict
from PIL import Image
from io import BytesIO
import re
import tempfile
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import requests
from bs4 import BeautifulSoup
import playwright.sync_api
from dotenv import load_dotenv
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

tavily_api_key=os.getenv("TAVILY_API_KEY")

callback_handler = StreamlitCallbackHandler(
                parent_container=st.container(),
                max_thought_containers=20,
                expand_new_thoughts=True,
                collapse_completed_thoughts=True
            )
            
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


class ResearchCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for research process."""
    
    def __init__(self):
        self.intermediate_steps = []
        self.current_tool = None
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Print out the prompts."""
        if not self.current_tool:  # Only show thinking for main steps, not tool usage
            st.write("🤔 Thinking...")
            with st.expander("View prompt", expanded=False):
                st.markdown(f"```\n{prompts[0]}\n```")
    
    def on_llm_end(self, response, **kwargs):
        """Print out the response."""
        if not self.current_tool:  # Only show done thinking for main steps
            st.write("✅ Done thinking")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Print out the tool and input."""
        self.current_tool = serialized['name']
        st.write(f"🔍 Using tool: {self.current_tool}")
        with st.expander(f"View {self.current_tool} input", expanded=False):
            st.markdown(f"```\n{input_str}\n```")
    
    def on_tool_end(self, output, **kwargs):
        """Print out the tool output."""
        with st.expander(f"View {self.current_tool} output", expanded=False):
            st.markdown(f"```\n{output}\n```")
        self.current_tool = None
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Print out the chain start."""
        chain_type = serialized.get("name", "Chain")
        if chain_type != "AgentExecutor":  # Don't show internal agent executor steps
            st.write(f"⚡ Starting {chain_type}")
        
    def on_chain_end(self, outputs, **kwargs):
        """Print out the chain end."""
        if not self.current_tool:  # Only show chain complete for main steps
            st.write("✅ Chain complete")
    
    def on_text(self, text, **kwargs):
        """Print out any additional text."""
        st.markdown(text)

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

class ResearchEngine:
    """Research engine that generates comprehensive reports."""

    def __init__(self, openai_api_key=None, tavily_api_key=None, max_sources=5, include_images=True):
        """Initialize the research engine."""
        load_dotenv()
        
        # Load API keys from environment if not provided
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set it in .env file or pass to constructor.")
        if not self.tavily_api_key:
            raise ValueError("Tavily API key is required. Set it in .env file or pass to constructor.")
        
        self.max_sources = max_sources
        self.include_images = include_images
        self.screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        
        # Ensure screenshots directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=self.openai_api_key,
            temperature=0,
            streaming=True
        )
        
    def create_research_plan(self, query: str, process_container: st.container) -> tuple[List[str], str]:
        """Create a research plan using the base LLM."""
        with process_container:
            st.write("📋 Creating research plan...")
            
            # Create callback handler for this step
            
            
            # prompt = ChatPromptTemplate.from_messages([
            #     ("system", """You are a scientist with a specialization in scientific writing. Main task: according to the key instructions below, you have to create a concise plan to gather information about the given topic. Assume that you might use only Web Search to create a report (web_search tool), no other sources are available. Create 4-5 concise steps how to gather information about the topic. Steps should cover different aspects of the output. Output this concise research plan."""),
            #     ("user", "Create a research plan for: {query}")
            # ])

            ### temp
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a scientist with a specialization in scientific writing. Main task: create 2 step concise plan to gather information about the given topic. Assume that you might use only Web Search to create a report (web_search tool), no other sources are available. """),
                ("user", "Create a research plan for: {query}")
            ])
            
            chain = prompt | self.llm
            
            response = chain.invoke({"query": query}, callbacks=[callback_handler])
            plan = [line.strip() for line in response.content.split('\n') if line.strip() and line[0].isdigit()]
            
            st.write("✅ Research plan created:")
            with st.expander("View research plan", expanded=False):
                st.write(f"```\n{response.content}\n```")
            
            return plan, response.content

    def setup_agent(self, process_container: st.container) -> AgentExecutor:
        """Set up the LangChain agent with necessary tools and prompt."""
        
        
        
        # Create search tool with callbacks
        search_tool = SearchTool(callback_handler=callback_handler)
        tools = [search_tool]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research assistant tasked to gather information on the given topic  according to this research plan:

            {plan}

            ### Follow these guidelines:
            1. Perform analysis step-by-step. Address each step in the research plan systematically.
            2. Most important: you have to rely on retrieved informaiton from web_search tool. For that, create a query for each step in the plan. Get relevant information for this step. If additional research is needed, create another query. 
            3. You might use tool more than 1 time per each step. 
            4. When you extracted relevant information, you have to cite sources inline at the end of the sentence. Use this format: sentence [Source](URL), where Source is the name of the source website (e.g. PubMed, ScienceDirect).
            5. Integrate information from multiple sources when possible.
            6. Never include the separate reference section. All citaitons should be mentioned directly in the text.
            7. Structure your response with appropriate headings (## Section Name)
            8. Ensure that for each step in the plan, you use the web_search tool at least once to gather information"""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def execute_research(self, query: str, plan: List[str], plan_all: str, process_container: st.container) -> str:
        """Execute the research using the LangChain agent with the research plan."""
        callback_handler = StreamlitCallbackHandler(
            parent_container=process_container,
            max_thought_containers=20,
            expand_new_thoughts=True,
            collapse_completed_thoughts=True
        )
        with process_container:
            st.write("🔍 Executing research plan...")
            agent = self.setup_agent(process_container)
            
            result = agent.invoke({
                "input": f"Research Query: {query}\nFollow the research plan to create a comprehensive report.",
                "plan": plan_all,
                
            }, 
        {
           'callbacks': [callback_handler]
        })
            
            st.write("✅ Research complete")
            return result["output"]

    def take_screenshot(self, url: str) -> Optional[str]:
        """Take a screenshot of the webpage."""
        try:
            # Generate a unique filename based on URL
            url_hash = hashlib.md5(url.encode()).hexdigest()
            filepath = os.path.join(self.screenshots_dir, f"{url_hash}.png")
            
            if os.path.exists(filepath):
                return filepath

            # Configure playwright
            with sync_playwright() as p:
                browser = p.chromium.launch()
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
                )
                
                # Create a new page with ad blocking
                page = context.new_page()
                
                try:
                    # Block common ad networks and trackers
                    page.route("**/(analytics|ads|google.*ads|doubleclick|facebook|tracking|metrics)/**", lambda route: route.abort())
                    
                    # Navigate to URL with timeout
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Wait for content to load
                    page.wait_for_timeout(2000)
                    
                    # Check for common error indicators
                    error_selectors = [
                        "text=Access Denied",
                        "text=403 Forbidden",
                        "text=404 Not Found",
                        "text=Error",
                        "text=Page Not Found",
                        "text=Service Unavailable",
                        "text=Bad Gateway",
                        "text=Gateway Timeout"
                    ]
                    
                    for selector in error_selectors:
                        try:
                            if page.locator(selector).count() > 0:
                                print(f"Error detected on page: {selector}")
                                return None
                        except Exception:
                            continue
                    
                    # Remove common cookie banners, ads, and popups
                    page.evaluate("""() => {
                        // Function to remove elements by selectors
                        const removeElements = (selectors) => {
                            selectors.forEach(selector => {
                                document.querySelectorAll(selector).forEach(element => {
                                    element.remove();
                                });
                            });
                        };
                        
                        // Common cookie notice and popup selectors
                        const selectors = [
                            '[class*="cookie"]',
                            '[class*="consent"]',
                            '[class*="popup"]',
                            '[class*="modal"]',
                            '[class*="banner"]',
                            '[class*="notification"]',
                            '[class*="subscribe"]',
                            '[class*="newsletter"]',
                            '[id*="cookie"]',
                            '[id*="consent"]',
                            '[id*="popup"]',
                            '[id*="modal"]',
                            '[id*="banner"]',
                            '[id*="notification"]',
                            '[id*="subscribe"]',
                            '[id*="newsletter"]'
                        ];
                        
                        removeElements(selectors);
                    }""")
                    
                    # Wait a bit for any animations to complete
                    page.wait_for_timeout(1000)
                    
                    # Take screenshot
                    page.screenshot(path=filepath)
                    
                    # Verify the screenshot is not just an error page
                    img_size = os.path.getsize(filepath)
                    if img_size < 5000:  # If file is suspiciously small
                        os.remove(filepath)
                        return None
                    
                    return filepath
                except Exception as e:
                    print(f"Error taking screenshot of {url}: {e}")
                    return None
                finally:
                    browser.close()
        except Exception as e:
            print(f"Error in screenshot process for {url}: {e}")
            return None

    def extract_urls_from_markdown(self, content: str) -> List[dict]:
        """Extract URLs and their context from markdown content."""
        url_pattern = r'(?P<url>https?://[^\s\)]+)'
        urls_with_context = []
        
        # Find all URLs and their positions
        for match in re.finditer(url_pattern, content):
            url = match.group('url')
            pos = match.start('url')
            
            # Find the sentence containing this URL
            sentence_start = pos
            while sentence_start > 0 and content[sentence_start-1] not in '.!?':
                sentence_start -= 1
            
            sentence_end = pos + len(url)
            while sentence_end < len(content) and content[sentence_end] not in '.!?':
                sentence_end += 1
            if sentence_end < len(content):
                sentence_end += 1
            
            context = content[sentence_start:sentence_end].strip()
            
            urls_with_context.append({
                'url': url,
                'position': pos,
                'context': context,
                'sentence_start': sentence_start,
                'sentence_end': sentence_end
            })
        
        return urls_with_context

    def generate_report(self, query: str) -> Report:
        """Generate a research report for the given query."""
        process_container = st.container()
        research_plan, research_plan_all = self.create_research_plan(query, process_container)
        content = self.execute_research(query, research_plan, research_plan_all, process_container)
        
        # Convert local image paths to base64 for Streamlit display
        def embed_image_streamlit(match):
            img_path = match.group(2)
            if os.path.isfile(img_path):
                try:
                    with open(img_path, "rb") as img_file:
                        img_data = base64.b64encode(img_file.read()).decode()
                        title = match.group(1).replace("Screenshot from ", "")
                        return f'<div class="image-container">\n<img src="data:image/png;base64,{img_data}" alt="{title}"/>\n<em>Source: {title}</em>\n</div>'
                except Exception as e:
                    print(f"Error embedding image {img_path}: {str(e)}")
            return match.group(0)
        
        # Process URLs and add screenshots
        sources = []
        urls_with_context = self.extract_urls_from_markdown(content)
        
        # Sort URLs by position and keep only first occurrence of each URL
        seen_urls = set()
        unique_urls_with_context = []
        for url_info in sorted(urls_with_context, key=lambda x: x['position']):
            if url_info['url'] not in seen_urls:
                seen_urls.add(url_info['url'])
                unique_urls_with_context.append(url_info)
        
        content_length_change = 0
        
        with st.spinner("📸 Taking screenshots of sources..."):
            for url_info in unique_urls_with_context:
                url = url_info['url']
                try:
                    st.write(f'Making screenshot of {url}')
                    
                    # Get webpage title and preview with timeout
                    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract title with fallbacks
                    title = None
                    og_title = soup.find('meta', property='og:title')
                    if og_title:
                        title = og_title.get('content')
                    if not title:
                        twitter_title = soup.find('meta', property='twitter:title')
                        if twitter_title:
                            title = twitter_title.get('content')
                    if not title and soup.title:
                        title = soup.title.string
                    if not title:
                        title = urlparse(url).netloc
                    title = title.strip() if title else url
                    
                    # Get preview text
                    article = soup.find('article') or soup.find('main') or soup.find('body')
                    preview_text = ''
                    if article:
                        article_text = article.get_text()
                        preview_text = ' '.join(article_text.split())[:200] + "..."
                    
                    # Take screenshot if enabled
                    screenshot_path = None
                    if self.include_images:
                        screenshot_path = self.take_screenshot(url)
                    
                    if screenshot_path:
                        sentence_end = url_info['sentence_end'] + content_length_change
                        
                        # Find the position after the last link in this sentence
                        sentence = content[url_info['sentence_start']:sentence_end]
                        last_link_end = 0
                        for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', sentence):
                            last_link_end = match.end()
                        
                        # Insert image after the last link or at sentence end
                        insert_pos = sentence_end
                        if last_link_end > 0:
                            insert_pos = url_info['sentence_start'] + last_link_end
                        
                        # Add title and image
                        image_html = (                            
                            "\n\n" +
                            f'<div class="image-container">\n'
                            f'<img src="data:image/png;base64,{base64.b64encode(open(screenshot_path, "rb").read()).decode()}" alt="Screenshot from {title}"/>\n'
                            f'<em>Source: {title}</em>\n'
                            f'</div>\n\n'
                        )
                        
                        content = content[:insert_pos] + image_html + content[insert_pos:]
                        content_length_change += len(image_html)
                    
                    sources.append(Source(
                        url=url,
                        title=title,
                        preview_text=preview_text,
                        screenshot_path=screenshot_path
                    ))
                    
                except Exception as e:
                    print(f"Error processing URL {url}: {str(e)}")
                    continue
        
        # Format the final content
        formatted_content = content.replace('\n\n\n', '\n\n')  # Remove excess newlines
        
        return Report(
            content=content,
            formatted_content=formatted_content,
            sources=sources,
            research_plan=research_plan
        )

    def create_downloadable_report(self, content: str, images_dir: str) -> bytes:
        """Create a downloadable version of the report with embedded images and preserved links."""
        try:
            # Create PDF with ReportLab
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
                textColor='#2a2a2a'
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor='#2a2a2a'
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=12,
                leading=16,
                spaceBefore=6,
                spaceAfter=12,
                textColor='#2a2a2a',
                alignment=4  # Justified text
            )
            caption_style = ParagraphStyle(
                'CustomCaption',
                parent=styles['Italic'],
                fontSize=10,
                leading=12,
                textColor='#666666',
                alignment=1  # Center alignment
            )
            
            # Build PDF content
            story = []
            
            # Add title
            story.append(Paragraph("Research Report", title_style))
            story.append(Spacer(1, 24))
            
            # Extract and process content
            current_text = ""
            image_pattern = r'<div class="image-container">\s*<img src="data:image/png;base64,([^"]+)"[^>]+>\s*<em>Source:\s*([^<]+)</em>\s*</div>'
            
            # Split content by image containers
            parts = re.split(image_pattern, content)
            
            for i in range(0, len(parts)):
                if i % 3 == 0:  # Text content
                    if parts[i].strip():
                        # Split text into paragraphs
                        paragraphs = parts[i].split('\n')
                        for paragraph in paragraphs:
                            if not paragraph.strip():
                                continue
                            
                            # Process headers
                            header_match = re.match(r'^##\s+(.+)$', paragraph)
                            if header_match:
                                header_text = header_match.group(1).strip()
                                story.append(Spacer(1, 12))
                                story.append(Paragraph(header_text, heading_style))
                                story.append(Spacer(1, 8))
                                continue
                            
                            # Process regular paragraphs with links
                            # Convert markdown to HTML
                            html = markdown.markdown(paragraph)
                            
                            # Process markdown links more carefully
                            def process_links(text):
                                # Keep track of all link positions to avoid overlapping replacements
                                links = []
                                for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', text):
                                    links.append((match.start(), match.end(), match.group(1), match.group(2)))
                                
                                # Replace links from end to start to maintain string indices
                                result = text
                                for start, end, title, url in reversed(links):
                                    link_html = f'<font color="blue">[<link href="{url}" color="blue">{title}</link>]</font>'
                                    result = result[:start] + link_html + result[end:]
                                
                                return result
                            
                            # Process links in text
                            html = process_links(paragraph)
                            
                            # Create paragraph with proper styling
                            para_style = ParagraphStyle(
                                'CustomParagraph',
                                parent=normal_style,
                                textColor='#2a2a2a',
                                spaceAfter=12,
                                leading=16
                            )
                            story.append(Paragraph(html, para_style))
                            story.append(Spacer(1, 4))
                elif i % 3 == 1:  # Image data
                    try:
                        # Process image
                        img_data = parts[i]
                        img_bytes = base64.b64decode(img_data)
                        img_buffer = BytesIO(img_bytes)
                        img = Image.open(img_buffer)
                        
                        # Calculate dimensions
                        max_width = 450
                        width, height = img.size
                        if width > max_width:
                            ratio = max_width / width
                            width = max_width
                            height = height * ratio
                        
                        # Add image and caption
                        story.append(Spacer(1, 12))
                        img = ReportLabImage(img_buffer, width=width, height=height)
                        story.append(img)
                        
                        # Add source caption (next part)
                        if i + 1 < len(parts):
                            story.append(Spacer(1, 6))
                            story.append(Paragraph(f"<i>Source: {parts[i+1]}</i>", caption_style))
                        
                        story.append(Spacer(1, 12))
                    except Exception as e:
                        print(f"Error processing image in PDF: {str(e)}")
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            raise

    def __del__(self):
        """Clean up resources."""
        pass
