FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////data/secureship.db

WORKDIR /app

# Create the non-root identity and writable runtime data directory first.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /nonexistent appuser \
    && mkdir -p /data \
    && chown appuser:appgroup /data

COPY requirements.txt ./requirements.txt

# Pin pip so future builds use a predictable installer version.
RUN python -m pip install --no-cache-dir "pip==26.2.1" \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./alembic.ini

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
