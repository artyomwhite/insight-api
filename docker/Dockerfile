# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/insight/.local/bin:$PATH"

RUN groupadd --gid 1000 insight && \
    useradd --uid 1000 --gid insight --create-home insight

WORKDIR /app

COPY --from=builder /install /home/insight/.local
COPY --chown=insight:insight . .

RUN chmod +x docker/entrypoint.sh

USER insight

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

ENTRYPOINT ["./docker/entrypoint.sh"]
