FROM python:3.11-slim
#system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# everything except mistralai
RUN grep -v "^mistralai==" requirements.txt > requirements_temp.txt && \
    pip install --no-cache-dir -r requirements_temp.txt && \
    rm requirements_temp.txt

# mistralai
RUN pip install --no-cache-dir mistralai==1.10.0

COPY . .
RUN mkdir -p storage/vectors
RUN mkdir -p /root/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Startup command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]