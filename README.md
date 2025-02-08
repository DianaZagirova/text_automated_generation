# 🔍 Web Research Assistant

Transform your research process with this powerful Streamlit application that leverages the intelligence of LangChain Agents and the latest AI technology to create comprehensive, well-structured reports from web sources. What sets this tool apart is its ability to not just gather information, but also automatically capture and include relevant images from source websites, making your reports more engaging and informative.

## ✨ Features

- 🤖 **Intelligent Web Research**: Powered by LangChain Agents for smart, context-aware information gathering
- 🖼️ **Automatic Image Collection**: Captures relevant images from source websites
- 📊 **Structured Reports**: Generates well-organized reports with customizable templates
- 🔗 **Rich Source Integration**: Includes source previews, citations, and screenshots
- 📱 **Social Sharing**: Built-in functionality for sharing on X (Twitter)
- ⬇️ **Export Options**: Download reports in PDF format

## 🚀 Setup with Docker Compose

1. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

2. Run with Docker Compose:
```bash
docker compose up
```

The application will be available at `http://localhost:8511`

Example app - https://dianazagirova-text-automated-generation-app-text-share-oqqy3z.streamlit.app/?embed_options=show_toolbar

## 💡 Usage2. Access the web interface:
   - Docker Compose: `http://localhost:8511`
   - Local setup: `http://localhost:8501`

3. Select your desired report template
4. Enter the research topic or company name
5. Click "Generate Report" and watch as the AI:
   - Conducts comprehensive web research
   - Captures relevant images from sources
   - Organizes information into a structured report
6. Review your report with:
   - Interactive source previews
   - Captured website screenshots
   - Full citations and references
7. Share your report:
   - Download as Markdown
   - Share directly to social media
   - Copy formatted text for other uses


## Environment Variables

Required environment variables:
```bash
OPENAI_API_KEY  # Your OpenAI API key
TAVILY_API_KEY  # Your Tavily API key - optional. Allows for Agent to search the web and collect links. When links are included in the report, the screenshots would be taken from those links automatically.

These can be set in a `.env` file for local development or passed as environment variables when running the Docker container.
