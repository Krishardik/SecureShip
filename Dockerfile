
# Start from a small official Python image to reduce unnecessary packages.
FROM python:3.10-slim

# Keep Python output visible in container logs and avoid .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install only the production dependencies declared by the project.
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copy the application and migration files with predictable ownership.
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./alembic.ini

# Store the SQLite database outside the application directory.
# The runtime should mount a writable volume at /data.
ENV DATABASE_URL=sqlite:////data/secureship.db

# Run as an unprivileged user instead of root.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /nonexistent appuser \
    && mkdir -p /data \
    && chown appuser:appgroup /data

USER appuser

EXPOSE 8000

# Start the FastAPI application using the production ASGI server.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

