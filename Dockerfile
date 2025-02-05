FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome Driver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | awk -F'.' '{print $1}') \
    && wget -q https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION} -O - | xargs -I {} \
    wget -q https://chromedriver.storage.googleapis.com/{}/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENV PYTHONPATH=/app
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
