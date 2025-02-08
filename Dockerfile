# Build stage
FROM python:3.11-bookworm as builder

# Set working directory
WORKDIR /app

# Install build dependencies with retry logic and package list cleanup
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    for i in {1..5}; do \
    (apt-get update -o Acquire::CompressionTypes::Order::=gz && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*) && break || \
    if [ $i -lt 5 ]; then \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    sleep 10; \
    else \
    exit 1; \
    fi; \
    done

# Copy requirements and install Python dependencies with retry logic
COPY requirements.txt .
RUN for i in {1..3}; do \
    pip install --no-cache-dir -r requirements.txt && break || \
    if [ $i -lt 3 ]; then sleep 5; else exit 1; fi; \
    done

# Final stage
FROM python:3.11-bookworm

# Set working directory
WORKDIR /app

# Configure apt for more reliable package downloads
RUN echo 'Acquire::CompressionTypes::Order:: "gz";' > /etc/apt/apt.conf.d/99compression && \
    echo 'Acquire::http::Pipeline-Depth "0";' > /etc/apt/apt.conf.d/99pipeline && \
    echo 'Acquire::http::No-Cache=True;' > /etc/apt/apt.conf.d/99nocache && \
    echo 'Acquire::BrokenProxy=true;' > /etc/apt/apt.conf.d/99brokenproxy

# Install runtime dependencies with improved retry logic
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    for i in {1..5}; do \
    (apt-get update -o Acquire::CompressionTypes::Order::=gz && \
    apt-get install -y --no-install-recommends --fix-missing \
    dbus \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*) && break || \
    if [ $i -lt 5 ]; then \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    sleep 10; \
    else \
    exit 1; \
    fi; \
    done

# Install Chromium in a separate layer with improved retry logic
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    for i in {1..5}; do \
    (apt-get update -o Acquire::CompressionTypes::Order::=gz && \
    apt-get install -y --no-install-recommends --fix-missing \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*) && break || \
    if [ $i -lt 5 ]; then \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    sleep 10; \
    else \
    exit 1; \
    fi; \
    done

# Create directories for templates and screenshots
RUN mkdir -p /app/templates /app/screenshots

# Copy Python packages from builder stage and install them globally
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:/usr/local/bin:$PATH" \
    CHROMIUM_PATH=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Start the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
