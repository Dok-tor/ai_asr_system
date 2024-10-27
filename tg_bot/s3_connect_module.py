import logging
import os
from aiogram.types import InputFile

import aiohttp

S3_URL = os.getenv('S3_URL')


async def send_file_to_s3(file_path: str, file_name: str, transcription_text: str):
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as file:
                # Создаем объект FormData для передачи файла и других данных
                form = aiohttp.FormData()
                form.add_field('file', file, filename=file_name, content_type='audio/wav')
                form.add_field('transcription', transcription_text)
                form.add_field('filename', file_name)

                # Отправляем POST-запрос
                async with session.post(url=f'{S3_URL}/upload-to-s3/', data=form) as response:
                    if response.status == 200:
                        logging.info(f"Successfully uploaded {file_name} to S3.")
                        return True
                    else:
                        logging.error(f'Error while sending file to S3: {response.status}')
                        return False
    except aiohttp.ClientError as e:
        logging.error(f'Connection to S3 error: {e}')
        return False
    except Exception as e:
        logging.error(f'Unexpected error: {e}')
        return False

