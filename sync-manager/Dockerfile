# Multi-stage build for production
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r syncuser && useradd -r -g syncuser syncuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/syncuser/.local

# Copy application code
COPY --chown=syncuser:syncuser . .

# Create necessary directories
RUN mkdir -p /data /logs /config && \
    chown -R syncuser:syncuser /data /logs /config

# Set environment variables
ENV PATH=/home/syncuser/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    LOG_FILE=/logs/sync_manager.log

# Switch to non-root user
USER syncuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Run the application
CMD ["python", "main.py"]
