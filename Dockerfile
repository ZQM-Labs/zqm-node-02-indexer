FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies (excluding Windows-only packages)
COPY requirements.txt .
RUN sed '/pywin32/d' requirements.txt > /tmp/reqs.txt && pip install --user --no-cache-dir -r /tmp/reqs.txt


FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app.py indexer.py ./
COPY templates/ ./templates/
COPY config.json .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Create directories for index and metadata storage
RUN mkdir -p /root/.zqm-node-02-indexer

# Health check using curl (more reliable than Python import)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f "http://127.0.0.1:5000/api/health" || exit 1

EXPOSE 5000

CMD ["python", "app.py"]
