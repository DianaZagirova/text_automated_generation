FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

# Create and switch to a working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose the port for Streamlit
EXPOSE 8511

# By default, this Docker image runs as root. For trusted code/tests, that's fine.
# If needed, create a separate user (pwuser) and switch to it for untrusted scenarios.

# Launch your Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8511", "--server.address=0.0.0.0"]