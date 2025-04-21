# opinion_analysis Dockerfile
FROM python:3.13-slim

WORKDIR /apps

# Install build dependencies first
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY apps/backend/requirements.txt backend_requirements.txt
COPY apps/frontend/requirements.txt frontend_requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r frontend_requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501