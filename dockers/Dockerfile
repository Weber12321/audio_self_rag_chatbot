# docker build -f dockers/Dockerfile -t timer_chatbot:develop .

# Dockerfile
FROM python:3.13-slim

WORKDIR /apps

# Install build dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY apps/requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt 

# Copy application code
COPY . .

# Expose port
EXPOSE 8501