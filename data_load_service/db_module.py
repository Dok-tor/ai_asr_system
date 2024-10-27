import logging
import os

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import s3_module as s3

# Настроим подключение к БД
db_user = os.environ['DB_USER']
db_pass = os.environ['DB_PASSWORD']
db_name = os.environ['DB_NAME']
db_host = os.environ['DB_HOST']

DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}/{db_name}"

engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем sessionmaker для управления сессиями
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Конфигурируем логгер
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Путь к локальной папке для загрузки
DOWNLOAD_DIR = os.environ['DOWNLOAD_DIR']
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def fetch_filenames_by_score(score: int):
    async with AsyncSessionLocal() as session:
        query = text("""
            SELECT pk FROM transcriptions WHERE score = :score
        """)
        result = await session.execute(query, {"score": score})
        filenames = [str(row["pk"]) for row in result.mappings()]
        return filenames


async def download_files():
    try:
        logging.info("Starting scheduled download from S3.")

        # Получаем списки файлов для каждого значения score
        score_folders = [0, 1, 2, 3]
        score_filenames = {score: await fetch_filenames_by_score(score) for score in score_folders}

        logging.info(f"Finished scheduled download from S3. {score_filenames}")

        # Проходим по всем значениям score и их спискам файлов
        for score, filenames in score_filenames.items():
            score_folder_path = os.path.join(DOWNLOAD_DIR, str(score))
            os.makedirs(score_folder_path, exist_ok=True)

            # Загружаем каждый файл из S3 и сохраняем в соответствующую папку
            for filename in filenames:
                local_folder_path = os.path.join(score_folder_path, filename)
                audio_file_name = f"{filename}_audio.wav"
                transcription_file_name = f"{filename}_transcription.txt"

                # Проверяем, если файлы уже существуют, пропускаем загрузку
                if os.path.exists(os.path.join(local_folder_path, audio_file_name)) and os.path.exists(os.path.join(local_folder_path, transcription_file_name)):
                    logging.info(f"Files for '{filename}' already exist in '{score_folder_path}', skipping download.")
                    continue

                # Создаем папку для файла
                os.makedirs(local_folder_path, exist_ok=True)

                # Загружаем файл из S3
                result = await s3.download_from_s3(filename, local_folder_path)
                if not result:
                    logging.error(f"Failed to download files for '{filename}' from S3.")
                    continue

                logging.info(f"Files for '{filename}' downloaded to '{score_folder_path}'.")

        logging.info("Scheduled download from S3 completed.")
    except Exception as e:
        logging.error(f"Error during scheduled download: {e}")


# Настраиваем планировщик APScheduler
scheduler = AsyncIOScheduler()

# Добавляем задачу в планировщик для выполнения каждые 24 часа
scheduler.add_job(download_files, 'interval', hours=3)

# Запускаем планировщик
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    scheduler.start()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
