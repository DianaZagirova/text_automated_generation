import streamlit as st

def init_states():
    if 'engine' not in st.session_state:
        st.session_state.engine = None
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = "dev"
    if 'tavily_api_key' not in st.session_state:
        st.session_state.tavily_api_key = ''
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ''
    return st.session_state
