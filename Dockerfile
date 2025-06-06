FROM python:3.10

# System config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Pre-install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY main.py requirements.txt ./          
COPY static/ ./static/

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Default port
ENV PORT=8000

# Run FastAPI
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]