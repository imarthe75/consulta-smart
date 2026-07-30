# Backend Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for ML, OCR, and document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    gfortran \
    curl \
    git \
    postgresql-client \
    libpq-dev \
    libopenblas-dev \
    liblapack-dev \
    libgomp1 \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Usuario no-root (hallazgo de seguridad, guía de remediación imarthe75 2026-07-29).
# uid 1000: docker-compose monta ./backend:/app como bind mount de desarrollo,
# propiedad del usuario del host (uid 1000).
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
