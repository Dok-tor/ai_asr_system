FROM python:3.12-slim

WORKDIR /app

# Установка необходимых пакетов
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get update && apt-get install -y ffmpeg

# Копируем файлы приложения
COPY . .

CMD ["python", "run_bot.py"]
