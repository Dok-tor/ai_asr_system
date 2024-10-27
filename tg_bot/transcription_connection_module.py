import logging
import os

import aiohttp

NN_API_URL = os.getenv('NN_API_URL')


async def get_prediction(temp_filename: str):
    try:
        async with aiohttp.ClientSession() as session:
            with open(temp_filename, 'rb') as audio_file:
                form = aiohttp.FormData()
                form.add_field('file', audio_file, content_type='audio/wav')

                async with session.post(url=NN_API_URL, data=form) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        prediction = result.get("prediction", "Ошибка предсказания")
                        return prediction
                    else:
                        logging.error(f'Enternal error: {resp.status}')
                        return None  # TODO свои классы ошибок
    except aiohttp.ClientError as e:
        logging.error(f'Connection to server error: {e}')
        return None
