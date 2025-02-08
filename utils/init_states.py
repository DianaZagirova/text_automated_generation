import streamlit as st
import os
def init_states():
    if 'engine' not in st.session_state:
        st.session_state.engine = None
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = "public" #"dev"
    if 'tavily_api_key' not in st.session_state:
        st.session_state.tavily_api_key = ''
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ''
    if 'include_images' not in st.session_state:
        st.session_state.include_images = True
    if 'screenshots_dir' not in st.session_state:
        st.session_state.screenshots_dir = os.path.join(os.getcwd(), "screenshots")        
    if 'custom_prompt' not in st.session_state:
        st.session_state.custom_prompt = ""
    return st.session_state
