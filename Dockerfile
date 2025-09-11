FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for audio + compiling pocketsphinx)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    swig \
    libpulse-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip & install deps
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
