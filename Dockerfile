FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/data \
    DATABASE_PATH=/app/data/users.db

RUN mkdir -p /app/data

# Сначала зависимости — слой кэшируется при изменении только кода
COPY python_bot/requirements.txt python_bot/requirements.txt
RUN pip install --no-cache-dir -r python_bot/requirements.txt

COPY python_bot/ python_bot/
COPY bot.sh bot_py.sh ./

# Telegram polling-бот, веб-порт не нужен
CMD ["python", "python_bot/main.py"]
