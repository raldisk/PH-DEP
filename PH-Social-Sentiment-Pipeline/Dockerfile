# Multi-stage Dockerfile
# Stage 1: builder
# Stage 2: runtime (lean, non-root)

FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local

COPY src/         ./src/
COPY transforms/  ./transforms/
COPY scripts/     ./scripts/
COPY dashboard/   ./dashboard/
COPY fixtures/    ./fixtures/
COPY pyproject.toml .

RUN pip install --no-cache-dir -e . --no-deps

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "ph_sentiment.pipeline"]
CMD ["--help"]
