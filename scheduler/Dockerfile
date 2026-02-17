FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scheduler.py .
COPY url_manager.py .

# Create directory for URLs file (will be mounted)
RUN mkdir -p /app/data

# Run as non-root user
RUN useradd -m -u 1000 scheduler && \
    chown -R scheduler:scheduler /app

USER scheduler

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-u", "scheduler.py"]