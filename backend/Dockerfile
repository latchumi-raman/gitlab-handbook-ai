# Python 3.11 slim — matches our dev environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed by lxml
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first
# (separate layer so Docker cache is reused on code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend source
COPY . .

# Render expects the app to listen on port 10000 by default
# We expose it here but the actual port comes from $PORT env var
EXPOSE 10000

# Health check — Render uses this to know when the container is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:${PORT:-10000}/api/v1/ping')" || exit 1

# Start command — reads PORT from Render's injected env var
CMD uvicorn api.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-10000} \
    --workers 1 \
    --log-level info