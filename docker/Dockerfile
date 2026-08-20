FROM python:3.12-slim

# Labels
LABEL maintainer="vedchaos"
LABEL version="3.3"
LABEL description="CHAOS TYPE ZERO v3.3 — Autonomous AI OS"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir playwright discord.py prometheus-client && \
    playwright install --with-deps chromium || true

# Copy application
COPY . .

# Create directories
RUN mkdir -p data/cache data/logs data/plugins data/db data/vault memory logs

# Expose ports
EXPOSE 8080 8081 9090

# Environment
ENV PYTHONUNBUFFERED=1
ENV CTZ_ENV=production
ENV CTZ_VERSION=3.3

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

# Default command
CMD ["python", "dashboard/server.py"]
