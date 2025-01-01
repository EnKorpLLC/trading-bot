# Use multi-stage build for smaller final image
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libpq-dev \
    python3-dev

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -s /bin/bash trader

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Set ownership
RUN chown -R trader:trader /app

# Switch to non-root user
USER trader

# Run application
CMD ["python", "-m", "src.app"] 