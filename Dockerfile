FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh
RUN groupadd --system app && useradd --system --gid app --create-home app && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
