FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY start.sh ./start.sh

RUN chmod +x /app/start.sh \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["./start.sh"]
