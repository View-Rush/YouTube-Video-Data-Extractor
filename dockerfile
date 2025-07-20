# Enhanced Multi-stage Docker build for YouTube Data Extractor
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
ENV GOOGLE_CLOUD_PROJECT_ID=""
ENV GCS_BUCKET_NAME="youtube-data-sri-lanka"
ENV BIGQUERY_DATASET_ID="youtube_analytics"
ENV BIGQUERY_TABLE_ID="video_data"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create application directories
WORKDIR /app
RUN mkdir -p /app/logs /app/data /app/static /app/templates \
    && chown -R appuser:appuser /app

# Copy application files
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser api_keys.json .
COPY --chown=appuser:appuser templates/ ./templates/

# Create directories for runtime data with proper permissions
RUN mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

# Switch to non-root user for security
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set default command with better configuration
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info", "--access-log"]
