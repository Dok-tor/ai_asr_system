FROM python:3.12-slim

# Устанавливаем зависимости
WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libpq-dev python3-dev && \
    python3 -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Скрипт, проверяющий и выполняющий миграции
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Запуск через entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
