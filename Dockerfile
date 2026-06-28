FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD sh -c 'python -c "import os,urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/api/v1/health\")"' || exit 1

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
