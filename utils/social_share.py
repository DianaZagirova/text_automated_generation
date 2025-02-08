import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from typing import Optional, List
from urllib.parse import quote
import glob
from PIL import Image
import io
import numpy as np
import random
import re

def extract_hashtags(text):
    # Regular expression pattern to match hashtags
    hashtag_pattern = r'#\w+'
    
    # Find all hashtags in the text
    hashtags = re.findall(hashtag_pattern, text)
    
    return [i.split('#')[1] for i in hashtags]

def create_twitter_share_button(text: str, url: Optional[str] = None, hashtags: Optional[str] = None) -> None:
    """Create a Twitter share button with custom text, URL, and hashtags."""
    # URL encode the text and prepare parameters
    encoded_text = quote(text)
    url_param = f"&url={quote(url)}" if url else ""
    hashtags_param = f"&hashtags={hashtags}" if hashtags else ""
    
    # Create the HTML for the Twitter share button
    html = f"""
        <div style="margin: 10px 0;">
            <a href="https://twitter.com/intent/tweet?text={encoded_text}{url_param}{hashtags_param}"
               onclick="window.open(this.href, '_blank', 'width=550,height=420,left=' + (screen.width/2-275) + ',top=' + (screen.height/2-210)); return false;"
               class="twitter-share-button"
               style="
                   display: inline-block;
                   background-color: #1DA1F2;
                   color: white;
                   padding: 10px 20px;
                   border-radius: 20px;
                   border: none;
                   text-decoration: none;
                   font-family: Arial, sans-serif;
                   font-weight: bold;
                   margin: 10px 0;
                   cursor: pointer;
                   transition: background-color 0.3s;
               "
               onmouseover="this.style.backgroundColor='#0d8bd9'"
               onmouseout="this.style.backgroundColor='#1DA1F2'"
            >
                <svg style="vertical-align: middle; margin-right: 5px;" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M12.6.75h2.454l-5.36 6.142L16 15.25h-4.937l-3.867-5.07-4.425 5.07H.316l5.733-6.57L0 .75h5.063l3.495 4.633L12.601.75Zm-.86 13.028h1.36L4.323 2.145H2.865l8.875 11.633Z"/>
                </svg>
                Share on X
            </a>
        </div>
    """
    
    # Render the button using Streamlit components
    components.html(html, height=70)

def create_share_section(report_content: str, screenshots_dir: str, limit_length: bool = False) -> None:
    """Create a section with social sharing options for the report."""
    if 'selected_images' not in st.session_state:
        st.session_state.selected_images = set()
    
    st.markdown("### 📤 Share Report")
    
    # Clean the content while preserving links and thread numbers
    def replace_link(match):
        """Format link to make the source name clickable"""
        text = match.group(1)  # This is the text inside []
        url = match.group(2)   # This is the URL inside ()
        
        text = text.strip('(').strip(')')
        return f"({text}: {url})"
    
    # Clean the content
    clean_content = re.sub(r'\[(.*?)\]\((.*?)\)', replace_link, report_content)  # Convert markdown links
    clean_content = re.sub(r'[*`]', '', clean_content)  # Remove markdown formatting except #
    clean_content = re.sub(r'<[^>]+>', '', clean_content)  # Remove HTML tags
    clean_content = re.sub(r'Source:.*?\n', '', clean_content)  # Remove source titles
    clean_content = re.sub(r'\n\s*\n+', '\n\n', clean_content)  # Normalize multiple newlines
    clean_content = clean_content.strip()
    
    # Split content into threads
    threads = re.split(r'(\d+/\d+[^\n]*\n)', clean_content)

    with st.expander("Preview tweet content"):
        st.text(clean_content)
    
    create_twitter_share_button(
        text=clean_content,
        hashtags=''
    )