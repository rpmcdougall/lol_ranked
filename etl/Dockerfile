# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file (if it exists) and install Python dependencies
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || echo "No requirements.txt found, skipping pip install"

# Copy the ETL script
COPY etl.py .

# Set the default command to run the ETL script
CMD ["python", "etl.py"] 