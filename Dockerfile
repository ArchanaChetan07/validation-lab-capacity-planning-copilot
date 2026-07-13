FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY static/ static/
COPY pyproject.toml .

ENV PYTHONPATH=/app/src
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/health', timeout=3)" || exit 1

CMD ["sh", "-c", "uvicorn capacity_copilot.api.main:app --host 0.0.0.0 --port ${PORT}"]
