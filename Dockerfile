FROM python:3.12-slim

# Install ffmpeg (required by yt-dlp for merging/converting)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create runtime directories
RUN mkdir -p downloads cache logs

# Non-root user for security
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

EXPOSE 8443

CMD ["python", "main.py"]
