# AI Research Assistant

An intelligent research assistant that generates comprehensive reports from web sources using AI, with specialized templates for business and pharmaceutical company analysis.

## Features

- Advanced web search using Tavily API
- Report generation with GPT-4
- Structured reports with customizable templates
- Source previews with citations
- Social sharing functionality for Twitter
- Downloadable reports in Markdown format
- Specialized templates for:
  - Business analysis
  - Pharmaceutical company deep dives
  - Research partnership strategies

## Setup

### Option 1: Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Chrome and ChromeDriver (for source previews):
```bash
brew install --cask google-chrome
brew install chromedriver
```

3. If you see a security warning about ChromeDriver, run:
```bash
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

4. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### Option 2: Docker Setup

1. Build the Docker image:
```bash
docker build -t ai-research-assistant .
```

2. Run the container:
```bash
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e TAVILY_API_KEY=your_tavily_api_key \
  ai-research-assistant
```

The application will be available at `http://localhost:8501`

## Usage

1. Run the application:
```bash
# Local setup
streamlit run app.py

# Or use Docker
docker run -p 8501:8501 ai-research-assistant
```

2. Choose a report template
3. Enter required information (e.g., company name)
4. Click "Generate Report"
5. View the generated report with sources
6. Share directly to Twitter or download in Markdown format

## Report Templates

### Business Analysis
- Company Overview
- Products & Services
- Market Presence & Competitors
- Innovation & Sustainability
- Future Outlook & Opportunities
- SWOT Analysis

### Pharmaceutical Company Analysis
- Corporate Profile & Strategic Positioning
- Global Offices & Facilities
- Therapeutic Portfolio
- Clinical Pipeline
- Research Infrastructure & Scientific Output
- Therapeutic Area Competition
- Partnerships, Politics & Policies
- Business Development Opportunities

## Social Sharing

Reports can be shared directly to Twitter with:
- Formatted source citations
- Clickable links to sources
- Clean text formatting

## Report Structure

Generated reports include:
- Title and Executive Summary
- Structured sections with clear headings
- Inline citations with source links
- Comprehensive analysis
- References section

## Development

The project uses:
- Python 3.8+
- Streamlit for the web interface
- OpenAI GPT-4 for text generation
- Tavily API for web search
- Custom templates in JSON format
- Docker for containerization

## Environment Variables

Required environment variables:
```bash
OPENAI_API_KEY  # Your OpenAI API key
TAVILY_API_KEY  # Your Tavily API key
```

These can be set in a `.env` file for local development or passed as environment variables when running the Docker container.
