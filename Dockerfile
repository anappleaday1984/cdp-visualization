# Multi-stage Dockerfile for CDP Visualization Framework
# This builds both FastAPI backend and Streamlit dashboard

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy application code
COPY --chown=appuser:appgroup api/ ./api/
COPY --chown=appuser:appgroup dashboard/ ./dashboard/
COPY --chown=appuser:appgroup monitoring/ ./monitoring/
COPY --chown=appuser:appgroup *.md ./
COPY --chown=appuser:appgroup requirements.txt ./

# Create data directory and link external data
RUN mkdir -p /app/data && \
    ln -sf /workspace/digital_twin/monitoring/data/behavior_twin_monthly.jsonl /app/data/behavior_twin_monthly.jsonl && \
    ln -sf /workspace/digital_twin/monitoring/data/daily_intel_report.jsonl /app/data/daily_intel_report.jsonl && \
    ln -sf /workspace/digital_twin/web_intel/daily_web_intel.jsonl /app/data/daily_web_intel.jsonl

# Switch to non-root user
USER appuser

# Expose ports
# 8000: FastAPI backend
# 8501: Streamlit dashboard
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Environment variables
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Default command (can be overridden)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 & streamlit run dashboard/app.py --server.port 8501 --server.headless true"]
