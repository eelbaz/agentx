# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make port 8501 available for Streamlit
EXPOSE 8501

# Create directory for temporary files
RUN mkdir -p /tmp/agentx

# Set environment variables for tools
ENV PYTHONPATH=/app

# Run the application
CMD ["streamlit", "run", "src/app.py", "--server.address", "0.0.0.0"] 