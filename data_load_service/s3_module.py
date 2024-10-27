import logging
import tempfile
import asyncio
from minio import Minio
from minio.error import S3Error
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
bucket_name = os.environ['BUCKET_NAME']
download_dir = os.environ['DOWNLOAD_DIR']

# Инициализируем клиента MinIO
minio_client = Minio(
    os.environ['S3_ADDRESS'],  # Адрес MinIO (имя контейнера и порт из docker-compose)
    access_key=os.environ['ACCESS_KEY'],  # MINIO_ACCESS_KEY
    secret_key=os.environ['SECRET_KEY'],  # MINIO_SECRET_KEY
    secure=False  # Используйте True, если у вас настроен HTTPS
)


async def upload_to_s3(audio_file_path: str, transcription_text: str, file_name: str):
    logging.info('Uploading audio and transcription to MinIO')
    # logging.info(f'transcription text: {transcription_text}')

    try:
        found = await asyncio.to_thread(minio_client.bucket_exists, bucket_name)
    except S3Error as e:
        logging.error(f"Error checking if bucket exists: {e}")
        return False

    if not found:
        await asyncio.to_thread(minio_client.make_bucket, bucket_name)
        logging.info(f"Bucket '{bucket_name}' was created.")
    else:
        logging.info(f"Bucket '{bucket_name}' already exists.")

    folder_name = file_name
    audio_file_name = f"{file_name}_audio.wav"
    transcription_file_name = f"{file_name}_transcription.txt"

    s3_audio_path = f"{folder_name}/{audio_file_name}"
    s3_transcription_path = f"{folder_name}/{transcription_file_name}"

    try:
        await asyncio.to_thread(
            minio_client.fput_object,
            bucket_name, s3_audio_path, audio_file_path, "audio/wav")
        logging.info(f"Audio file '{s3_audio_path}' uploaded successfully.")
    except S3Error as e:
        logging.error(f"Error uploading audio file: {e}")
        return False

    try:
        with tempfile.NamedTemporaryFile(mode="w") as temp_file:
            temp_file.write(transcription_text)
            temp_file.flush()
            temp_file_path = temp_file.name

            await asyncio.to_thread(
                minio_client.fput_object,
                bucket_name, s3_transcription_path, temp_file_path, "text/plain"
            )
            logging.info(f"Transcription file '{s3_transcription_path}' uploaded successfully.")
    except S3Error as e:
        logging.error(f"Error uploading transcription: {e}")
        return False

    return True


async def download_from_s3(filename: str, local_folder_path: str):
    logging.info(f"Downloading '{filename}' from S3.")

    audio_file_name = f"{filename}_audio.wav"
    transcription_file_name = f"{filename}_transcription.txt"

    s3_audio_path = f"{filename}/{audio_file_name}"
    s3_transcription_path = f"{filename}/{transcription_file_name}"

    local_audio_path = os.path.join(local_folder_path, audio_file_name)
    local_transcription_path = os.path.join(local_folder_path, transcription_file_name)

    try:
        await asyncio.to_thread(
            minio_client.fget_object, bucket_name, s3_audio_path, local_audio_path
        )
        logging.info(f"Audio file '{s3_audio_path}' downloaded successfully.")
    except S3Error as e:
        logging.error(f"Error downloading audio file: {e}")
        return False

    try:
        await asyncio.to_thread(
            minio_client.fget_object, bucket_name, s3_transcription_path, local_transcription_path
        )
        logging.info(f"Transcription file '{s3_transcription_path}' downloaded successfully.")
    except S3Error as e:
        logging.error(f"Error downloading transcription: {e}")
        return False

    logging.info(f"All files for '{filename}' downloaded successfully.")
    return True


addition_dir = "/raw_files"


async def download_all_files_from_s3():
    try:
        # Проверяем наличие бакета
        bucket_exists = await asyncio.to_thread(minio_client.bucket_exists, bucket_name)
        if not bucket_exists:
            logging.error(f"Bucket '{bucket_name}' does not exist.")
            return False

        # Получаем список всех объектов в бакете
        objects = await asyncio.to_thread(minio_client.list_objects, bucket_name, recursive=True)

        # Загружаем каждый объект в локальную папку
        for obj in objects:
            local_file_path = os.path.join(download_dir+addition_dir, obj.object_name)
            local_folder = os.path.dirname(local_file_path)
            os.makedirs(local_folder, exist_ok=True)

            try:
                # Загружаем файл из S3
                await asyncio.to_thread(minio_client.fget_object, bucket_name, obj.object_name, local_file_path)
                logging.info(f"Downloaded '{obj.object_name}' to '{local_file_path}'.")
            except S3Error as e:
                logging.error(f"Error downloading '{obj.object_name}': {e}")

        logging.info("All files downloaded successfully.")
        return True

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False