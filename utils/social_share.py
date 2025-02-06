import streamlit as st
import streamlit.components.v1 as components
import base64
import os
from typing import Optional, List
from urllib.parse import quote
import glob
from PIL import Image
import re

def create_twitter_share_button(text: str, url: Optional[str] = None, hashtags: Optional[List[str]] = None) -> None:
    """Create a Twitter share button with custom text, URL, and hashtags.
    
    Args:
        text (str): The text content to share on Twitter
        url (Optional[str]): The URL to include in the tweet
        hashtags (Optional[List[str]]): List of hashtags to include in the tweet
    """
    # URL encode the text and prepare parameters
    encoded_text = quote(text)
    url_param = f"&url={quote(url)}" if url else ""
    hashtags_param = f"&hashtags={','.join(hashtags)}" if hashtags else ""
    
    # Create the HTML for the Twitter share button with JavaScript to open in new window
    html = f"""
        <div style="margin: 10px 0;">
            <a href="#"
               onclick="window.open('https://twitter.com/intent/tweet?text={encoded_text}{url_param}{hashtags_param}', '_blank', 'width=550,height=420'); return false;"
               class="twitter-share-button"
               data-size="large"
               style="
                   display: inline-block;
                   background-color: #1DA1F2;
                   color: white;
                   padding: 10px 20px;
                   border-radius: 20px;
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

def load_and_convert_image(image_path: str) -> Image.Image:
    """Load and convert image to RGB if necessary."""
    with Image.open(image_path) as img:
        if img.mode in ('RGBA', 'LA'):
            return img.convert('RGB')
        return img.copy()

def create_share_section(report_content: str, screenshots_dir: str) -> None:
    """Create a section with social sharing options for the report.
    
    Args:
        report_content (str): The content of the report to share
        screenshots_dir (str): Directory containing any screenshots to be shared
    """
    # Initialize session state for selected images if not exists
    if 'selected_images' not in st.session_state:
        st.session_state.selected_images = set()
    
    st.markdown("### 📤 Share Report")
    
    # Create a clean version of the report for social media
    # Remove markdown formatting and citations for cleaner sharing
    
    # Remove markdown links and keep just the text
    clean_content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', report_content)
    # Remove other markdown formatting
    clean_content = re.sub(r'[#*`]', '', clean_content)
    clean_content = clean_content.strip()
    
    # Get available screenshots
    screenshots = glob.glob(os.path.join(screenshots_dir, "*.png"))
    
    # Create tabs for different sharing options
    text_tab, media_tab = st.tabs(["📝 Share Text", "🖼️ Share with Images"])
    
    # Default hashtags for research reports
    hashtags = ["Research", "Science", "AI"]
    
    with text_tab:
        st.markdown("Share the full research report:")
        create_twitter_share_button(
            text=clean_content,
            hashtags=hashtags
        )
    
    with media_tab:
        if screenshots:
            st.markdown("Select images to share with your report:")
            
            # Create columns for the grid layout
            cols = st.columns(2)
            
            for idx, screenshot_path in enumerate(screenshots):
                try:
                    with cols[idx % 2]:
                        # Create a unique key for the image
                        image_key = f"img_{os.path.basename(screenshot_path)}"
                        
                        # Load and display image
                        try:
                            img = load_and_convert_image(screenshot_path)
                            st.image(img, use_column_width=True)
                        except Exception as e:
                            st.error(f"Error loading image: {os.path.basename(screenshot_path)}")
                            continue
                        
                        # Checkbox for selection, using session state
                        if st.checkbox("Select this image", 
                                     key=image_key,
                                     value=image_key in st.session_state.selected_images):
                            st.session_state.selected_images.add(image_key)
                            
                            # Create share button for this image
                            image_preview = clean_content[:100] + "..."
                            create_twitter_share_button(
                                text=image_preview,
                                hashtags=hashtags
                            )
                        else:
                            if image_key in st.session_state.selected_images:
                                st.session_state.selected_images.remove(image_key)
                except Exception as e:
                    st.error(f"Error processing image: {os.path.basename(screenshot_path)}")
        else:
            st.info("No images available for this report.")
