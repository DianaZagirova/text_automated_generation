import os
import base64
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.callbacks import StreamlitCallbackHandler
import streamlit as st
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse
from utils.agent_tools import SearchTool
from utils.schemas import Source, Report
from utils.take_screenshots import take_screenshots
import json
import requests

tavily_api_key=os.getenv("TAVILY_API_KEY")

callback_handler = StreamlitCallbackHandler(
                parent_container=st.container(),
                max_thought_containers=20,
                expand_new_thoughts=True,
                collapse_completed_thoughts=True
            )  

class ResearchEngine:
    """Research engine that generates comprehensive reports."""

    def __init__(self, report_type, openai_api_key=None, tavily_api_key=None, max_sources=5, include_images=True, model="gpt-4o-mini", temperature=0.5):
        """Initialize the research engine."""
        load_dotenv()     
        

        types_mapping = {"Brief report":'research', "Twitter post":"x_post"}  
        
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set it in .env file or pass to constructor.")
        if not self.tavily_api_key:
            raise ValueError("Tavily API key is required. Set it in .env file or pass to constructor.")
        
        self.max_sources = max_sources
        self.include_images = include_images
        self.screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        self.model = model
        self.temperature = temperature
        
        self.prompts = json.load(open("./prompts/prompts.json", "r"))
        self.report_type = types_mapping.get(report_type)
        self.plan_prompt = self.prompts[self.report_type]["plan_prompt"]
        self.prompt = self.prompts[self.report_type]["prompt"] 
        

        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.openai_api_key,
            temperature=self.temperature,
            streaming=True
        )
        
    def create_research_plan(self, query: str, process_container: st.container) -> tuple[List[str], str]:
        """Create a research plan using the base LLM."""
        with process_container:
            st.write("📋 Creating research plan...")

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.plan_prompt),
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

        search_tool = SearchTool(callback_handler=callback_handler)
        tools = [search_tool]

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt),
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
        return take_screenshots(url, self.screenshots_dir)

    def extract_urls_from_markdown(self, content: str) -> List[Dict]:
        """Extract URLs and their context from markdown content, handling multiple URLs per sentence."""
        url_pattern = r'(?P<url>https?://[^\s\)]+)'
        url_matches = list(re.finditer(url_pattern, content))
        urls = []
        
        # Collect all URLs with their start and end positions
        for match in url_matches:
            start = match.start('url')
            end = match.end('url')
            url = match.group('url')
            urls.append({'url': url, 'start': start, 'end': end})
        
        urls_with_context = []
        
        for url_info in urls:
            url = url_info['url']
            pos = url_info['start']
            end_pos = url_info['end']
            
            # Find sentence_start
            sentence_start = pos
            while sentence_start > 0:
                prev_char_pos = sentence_start - 1
                prev_char = content[prev_char_pos]
                if prev_char in '.!?':
                    # Check if this punctuation is within any URL
                    inside_url = any(u['start'] <= prev_char_pos < u['end'] for u in urls)
                    if not inside_url:
                        sentence_start = prev_char_pos + 1  # Start after the punctuation
                        break
                sentence_start -= 1
            
            # Find sentence_end
            sentence_end = end_pos
            while sentence_end < len(content):
                curr_char = content[sentence_end]
                if curr_char in '.!?':
                    # Check if this punctuation is within any URL
                    inside_url = any(u['start'] <= sentence_end < u['end'] for u in urls)
                    if not inside_url:
                        sentence_end += 1  # Include the punctuation
                        break
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

        # Process URLs and add screenshots
        sources = []
        urls_with_context = self.extract_urls_from_markdown(content)
        
        # Sort URLs by position and keep only first occurrence of each URL
        seen_urls = set()
        unique_urls_with_context = []
        for url_info in sorted(urls_with_context, key=lambda x: (x['sentence_start'], -x['position'])):
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
                        
                        if content[:insert_pos+1][-1] == ".":
                            insert_pos += 1

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
                    print(f"[ERROR] Error processing URL {url}: {str(e)}")
                    continue
        
        formatted_content = content.replace('\n\n\n', '\n\n')  # Remove excess newlines
        
        return Report(
            content=content,
            formatted_content=formatted_content,
            sources=sources,
            research_plan=research_plan
        )

    