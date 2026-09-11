# Multi-stage unprivileged Dockerfile for Smart Traffic Simulator

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY config.py main.py stats.py ./
COPY core/ core/
COPY render/ render/

RUN pip install --no-cache-dir --upgrade pip build && \
    python -m build --wheel && \
    pip install --no-cache-dir --prefix=/install dist/*.whl


FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SDL_VIDEODRIVER=dummy

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser && \
    mkdir -p /app /app/output && \
    chown -R appuser:appgroup /app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder --chown=appuser:appgroup /build /app

USER 10001:10001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD smart-traffic --headless --autoquit 0.1 --seed 42 || exit 1

ENTRYPOINT ["smart-traffic"]
CMD ["--headless", "--autoquit", "10.0"]
