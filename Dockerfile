FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py instapaper_client.py wsgi.py ./
COPY templates ./templates
COPY static ./static

RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "120"]
