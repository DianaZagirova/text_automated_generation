import streamlit as st
st.set_page_config(
        page_title="Research Assistant",
        page_icon="🔍",
        layout="wide"
    )

from dotenv import load_dotenv
import os
import hashlib
import base64
from datetime import datetime
import shutil
import tempfile
import markdown
import re

from research_engine import ResearchEngine

    
# Load environment variables
load_dotenv()

def get_download_link(content, filename, mime_type):
    """Generate a download link for the content."""
    b64_content = base64.b64encode(content).decode() if isinstance(content, bytes) else base64.b64encode(content.encode()).decode()
    href = f'data:{mime_type};base64,{b64_content}'
    return f'<a href="{href}" class="download-button" download="{filename}">📥 Download PDF Report</a>'

def main():
    

    # Initialize research engine at the start
    try:
        engine = ResearchEngine()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please make sure you have set up your API keys in the .env file.")
        return

    # Custom CSS for the entire app
    st.markdown("""
        <style>
        /* Global styles */
        .stApp {
            background-color: #f5f5f5;
        }
        
        /* Make tabs larger and more prominent */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            padding: 0 0px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: auto;
            min-width: 360px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px;
            margin: 0;
            padding: 10px 24px;
            font-size: 16px;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #e0e2e6;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #445549;
            color: white;
        }
        
        /* Improve spacing and readability */
        .stTabs [data-baseweb="tab-panel"] {
            padding: 24px 0;
        }
        
        /* Main content area styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Report container styling */
        .report-container {
            background-color: white;
            padding: 2.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
        }

        /* Report content styling */
        .report-content {
            font-size: 16px;
            line-height: 1.8;
            color: #2a2a2a;
        }

        .report-content h1 {
            color: #1a1a1a;
            font-size: 32px;
            margin: 1.5rem 0;
            font-weight: 600;
            border-bottom: 2px solid #445549;
            padding-bottom: 0.5rem;
        }

        .report-content h2 {
            color: #2a2a2a;
            font-size: 24px;
            margin: 2rem 0 1rem;
            font-weight: 500;
        }

        .report-content p {
            margin-bottom: 1.2rem;
            text-align: justify;
        }

        .report-content a {
            color: #445549;
            text-decoration: none;
            border-bottom: 1px solid #445549;
            transition: all 0.2s ease;
        }

        .report-content a:hover {
            color: #2a2a2a;
            border-bottom: 2px solid #2a2a2a;
        }

        /* Image container styling */
        .image-container {
            margin: 2rem 0;
            text-align: center;
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .image-container img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }

        .image-container em {
            display: block;
            margin-top: 1rem;
            color: #666;
            font-style: italic;
            font-size: 14px;
        }

        /* Download button styling */
        .download-button {
            display: inline-block;
            background-color: #e3e3e3;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            margin: 1rem 0;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .download-button:hover {
            background-color: #a8a8a8;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-1px);
        }

        /* Override Streamlit's default background */
        .stApp > header {
            background-color: transparent;
        }

        .stApp > div:has(>.element-container) {
            background-color: #f5f5f5;
        }

        /* Make the report section stand out */
        div[data-testid="stVerticalBlock"] > div:has(> .report-container) {
            background-color: #f5f5f5;
            padding: 2rem;
            border-radius: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🔍 AI Researcher")
    
    # Input section
    with st.container():
        query = st.text_area("Enter your research topic:", height=100)
        
        if st.button("🚀 Generate Report", type="primary", use_container_width=True):
            if not query:
                st.error("Please enter a research topic")
                return
            
            try:
                # Create a container for the research process
                process_container = st.container()
                
                with st.spinner("🎯 Initializing research process..."):
                    report = engine.generate_report(query)
                    st.session_state.report = report
                    # Store engine in session state for PDF generation
                    st.session_state.engine = engine
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                return

    # Display research results
    if hasattr(st.session_state, 'report') and st.session_state.report:
        report = st.session_state.report
        
        # Create tabs for process and results
        process_tab, report_tab, sources_tab = st.tabs(["🔄 Agent's thoughts", "📝 Report", "📚 Sources"])
        
        with process_tab:
            st.markdown("### Research Progress")
            st.markdown("✅ Research plan created and executed")
            with st.expander("View Research Plan", expanded=False):
                for i, step in enumerate(report.research_plan, 1):
                    st.markdown(f"{i}. {step}")
        
        with report_tab:
            st.markdown("## Research Report", unsafe_allow_html=True)
            
            # Display the report in a container with proper HTML rendering
            st.markdown(
                f'<div class="report-container">'
                f'<div class="report-content">{report.content}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # Add download section
            st.markdown("### Download Report")
            try:
                with st.spinner("📑 Preparing PDF download..."):
                    print(report.content)
                    pdf_content = engine.create_downloadable_report(report.content, engine.screenshots_dir)
                    if not isinstance(pdf_content, bytes):
                        pdf_content = pdf_content.encode()
                    
                    # Get current timestamp for filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"research_report_{timestamp}.pdf"
                    
                    # Create download button
                    st.markdown(
                        get_download_link(pdf_content, filename, "application/pdf"),
                        unsafe_allow_html=True
                    )
            except Exception as e:
                st.error(f"Error creating PDF: {str(e)}")
        
        with sources_tab:
            st.markdown("### Source Materials")
            for source in report.sources:
                with st.expander(f"📄 {source.title}", expanded=False):
                    st.markdown(f"**URL:** [{source.url}]({source.url})")
                    st.markdown(f"**Preview:** {source.preview_text}")
                    if source.screenshot_path and os.path.exists(source.screenshot_path):
                        try:
                            st.image(source.screenshot_path, caption=f"Screenshot of {source.title}", use_column_width=True)
                        except Exception as e:
                            st.error(f"Could not load preview image: {str(e)}")

if __name__ == "__main__":
    main()
