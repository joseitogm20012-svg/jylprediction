FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r scrapycoco && useradd -r -g scrapycoco -m -d /home/scrapycoco scrapycoco

FROM base AS builder

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM base AS playwright-deps

RUN pip install --no-cache-dir --user playwright && \
    python -m playwright install chromium --with-deps && \
    rm -rf /root/.cache /tmp/*

FROM base AS final

COPY --from=builder /root/.local /home/scrapycoco/.local
COPY --from=playwright-deps /root/.local /home/scrapycoco/.local
COPY --from=playwright-deps /root/.cache/ms-playwright /home/scrapycoco/.cache/ms-playwright

ENV PATH=/home/scrapycoco/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/home/scrapycoco/.cache/ms-playwright \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --chown=scrapycoco:scrapycoco . .

RUN mkdir -p /app/data /app/scrapycoco && chown -R scrapycoco:scrapycoco /app

USER scrapycoco

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3006/api/scrapers || exit 1

EXPOSE 3006

CMD ["python", "main.py"]
