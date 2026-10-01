# Madare Emrooz API. Build from the backend/ folder:
#   docker build -t madare-emrooz-backend .                 # production image
#   docker build --target test -t madare-emrooz-test .      # image with the test suite

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# --- tests: run with a PostgreSQL in TEST_DATABASE_URL (see docker-compose.test.yml) ---
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
CMD ["python", "-m", "pytest", "-q", "-W", "error"]

# --- production ---
FROM base AS runtime
RUN useradd --create-home --uid 10001 app
COPY --chown=app:app app ./app
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app wsgi.py docker-entrypoint.sh ./
USER app
ENV FLASK_APP=wsgi.py \
    GUNICORN_WORKERS=3
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(urllib.request.urlopen('http://127.0.0.1:5000/api/v1/health', timeout=4).status != 200)"
ENTRYPOINT ["./docker-entrypoint.sh"]
# Uploads are up to 10 MB, so allow slow clients a little longer than gunicorn's default.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS} --timeout 60 --access-logfile - --error-logfile - wsgi:app"]
