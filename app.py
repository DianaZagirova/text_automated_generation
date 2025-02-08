import streamlit as st
st.set_page_config(
        page_title="Research Assistant",
        page_icon="🔍",
        layout="wide"
    )

from dotenv import load_dotenv
import os
import base64
from datetime import datetime

from research_engine import ResearchEngine
from utils.formatting import apply_formatting
from utils.download_report import create_downloadable_report
from utils.social_share import create_share_section
from utils.init_states import init_states

load_dotenv()
apply_formatting()
init_states()

def get_download_link(content, filename, mime_type):
    """Generate a download link for the content."""
    b64_content = base64.b64encode(content).decode() if isinstance(content, bytes) else base64.b64encode(content.encode()).decode()
    href = f'data:{mime_type};base64,{b64_content}'
    return f'<a href="{href}" class="download-button" download="{filename}">📥 Download PDF Report</a>'

def main():      
    
    st.title("🔍 AI Researcher")   
    if st.session_state.app_mode == "dev":
        st.session_state.tavily_api_key = os.getenv("TAVILY_API_KEY")
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY")
    else:
        st.session_state.tavily_api_key = st.input_text("Tavily API Key:")
        st.session_state.openai_api_key = st.input_text("OpenAI API Key:")
    if not st.session_state.tavily_api_key or not st.session_state.openai_api_key:
        return
    
    with st.container():
        col1, col2 = st.columns([5,1])
        with col1:
            query = st.text_area("Enter your research topic:", height=100)
        with col2:
            report_type = st.radio("Select a report type:", [ "Twitter post" , "Brief report"], horizontal=True)
        
        if st.button("🚀 Generate Report", type="primary", use_container_width=True):
            if not query:
                st.error("Please enter a research topic")
                return            
            try:            
                with st.spinner("🎯 Initializing research process..."):
                    # Initialize research engine
                    try:
                        engine = ResearchEngine(report_type=report_type)
                        st.session_state.engine = engine  # Store engine in session state
                    except ValueError as e:
                        st.error(f"Configuration Error: {str(e)}")
                        st.info("Please make sure you have set up your API keys in the .env file.")
                        return     

                    report = engine.generate_report(query)
                    st.session_state.report = report
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
                    st.markdown(f"{step}")
        
        with report_tab:
            st.markdown("## Research Report", unsafe_allow_html=True)
            st.markdown(
                f'<div class="report-container">'
                f'<div class="report-content">{report.content}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("### Download Report")
            try:
                with st.spinner("📑 Preparing PDF download..."):
                    if not hasattr(st.session_state, 'engine'):
                        st.error("Research engine not initialized. Please generate a report first.")
                        return
                    print(report.content)
                    pdf_content = create_downloadable_report(report.content, st.session_state.engine.screenshots_dir)
                    if not isinstance(pdf_content, bytes):
                        pdf_content = pdf_content.encode()                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"research_report_{timestamp}.pdf"                    
                    st.markdown(
                        get_download_link(pdf_content, filename, "application/pdf"),
                        unsafe_allow_html=True
                    )
            except Exception as e:
                st.error(f"Error creating PDF: {str(e)}")

            # Add social sharing section
            create_share_section(report.content, st.session_state.engine.screenshots_dir)
        
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
