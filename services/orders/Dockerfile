FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy shared modules
COPY shared/ /app/shared/

# Copy service code
COPY services/orders/ /app/services/orders/

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=services.orders.app

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Run the application
CMD ["python", "/app/services/orders/app.py"]
