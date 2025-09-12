FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg and system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    swig \
    libpulse-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU wheels (matching versions available in index)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
       torch==2.4.0 \
       torchaudio==2.4.0 \
       -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Copy requirements separately for caching
COPY requirements.txt .

# Install the rest of requirements (gradio, whisper, etc.)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
