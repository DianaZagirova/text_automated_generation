import streamlit as st 

def apply_formatting():
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
