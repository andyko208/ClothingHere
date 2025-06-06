FROM python:3.10-slim

# Prevent .pyc files & enable real-time logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy code into container
COPY . /app

# Install system packages for image processing
RUN apt-get update && apt-get install -y \
    build-essential libglib2.0-0 libsm6 libxrender1 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set default port if not provided
ENV PORT=8000

# Start the FastAPI app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]