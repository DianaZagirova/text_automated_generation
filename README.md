# AI Research Assistant

An intelligent research assistant that generates comprehensive reports from web sources using AI.

## Features

- Web search using Tavily API
- Report generation with GPT-4
- Source previews with screenshots
- Structured reports with citations
- Downloadable reports in Markdown format

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Chrome and ChromeDriver:
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

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Enter your research topic or question
3. Click "Generate Report"
4. View the generated report and sources
5. Download the report in Markdown format

## Report Structure

The generated reports include:
- Executive Summary
- Logical sections with clear headings
- Inline citations with source links
- Figures with captions and attributions
- Conclusions
- References section

## Screenshots

Screenshots of web sources are automatically captured and stored in the `screenshots` directory.
