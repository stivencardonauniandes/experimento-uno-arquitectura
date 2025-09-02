FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy shared modules
COPY shared/ /app/shared/

# Copy service code
COPY services/monitor/ /app/services/monitor/

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1

# Run the application
CMD ["python", "/app/services/monitor/app.py"]
