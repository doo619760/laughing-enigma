# Legal Citation QA System - Dockerfile
# Python 3.11 slim base image for production deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /data/reports /data/audit /tmp/citation-qa /var/log/citation-qa

# Create non-root user for security
RUN useradd -m -u 1000 qauser && \
    chown -R qauser:qauser /app /data /tmp/citation-qa /var/log/citation-qa

# Switch to non-root user
USER qauser

# Expose webhook server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command: run webhook server
CMD ["python", "src/webhook_server.py"]
