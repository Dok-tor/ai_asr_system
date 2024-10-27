FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

WORKDIR /app

# Установка необходимых пакетов
COPY requirements.txt .
RUN apt-get update && apt-get install -y ffmpeg && \
    python3 -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем файлы приложения
COPY . .

# Запускаем FastAPI сервер
CMD ["uvicorn", "api_model:app", "--host", "0.0.0.0", "--port", "8000"]
