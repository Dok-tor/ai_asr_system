FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libpq-dev python3-dev supervisor && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Копируем файлы приложения
COPY . .

# Копируем конфигурационный файл supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Создаем папку для сохранения файлов
RUN mkdir -p /app/saved_files

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
#CMD ["sh", "-c", "python db_module.py && exec uvicorn run:app --host 0.0.0.0 --port 8001"]
## Запуск FastAPI сервиса
#CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8001"]
