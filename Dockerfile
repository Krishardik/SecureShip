FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////data/secureship.db

WORKDIR /app

# Create a non-root user and the writable runtime data directory.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /nonexistent appuser \
    && mkdir -p /data \
    && chown appuser:appgroup /data

COPY requirements.txt ./requirements.txt

# Install pinned dependencies, then remove pip and its bundled libraries.
# The application does not need a package installer at runtime.
RUN python -m pip install --no-cache-dir "pip==26.2.1" \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && rm -rf \
        /usr/local/lib/python3.10/site-packages/pip \
        /usr/local/lib/python3.10/site-packages/pip-*.dist-info \
        /usr/local/bin/pip \
        /usr/local/bin/pip3 \
        /usr/local/bin/pip3.10

COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./alembic.ini

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
