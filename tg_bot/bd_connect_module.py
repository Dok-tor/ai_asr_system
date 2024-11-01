import logging
import os

import aiohttp

BD_API_URL = os.getenv('BD_API_URL')


async def register_user(user_id):
    try:
        async with aiohttp.ClientSession() as session:
            user_data = {
                "tg_id": user_id,  # ID пользователя Telegram
                "cash": 0,  # Примерный score
                "role": 0  # Название файла
            }
            logging.info(f'user ID: {user_id}')
            async with session.post(url=f'{BD_API_URL}/register-user/', json=user_data) as resp:
                if resp.status == 200:
                    logging.info(f"User {user_id} registered")
                else:
                    logging.error(f'Error while registering user: {resp.status}')
    except aiohttp.ClientError as e:
        logging.error(f"FastAPI connection error: {e}")


async def add_transcription(user_id: int, duration_seconds: int):
    try:
        async with aiohttp.ClientSession() as session:
            transcription_data = {
                'user_tg_id': user_id,
                'score': 0,
                'duration_seconds': duration_seconds,
            }
            async with session.post(url=f'{BD_API_URL}/add-transcription/', json=transcription_data) as resp:
                if resp.status == 200:
                    logging.info(f"Transcription from user_id {user_id} added")
                    return await resp.json()
                else:
                    logging.error(f"Error while adding transcription: {resp.status}")
                    return None

    except aiohttp.ClientError as e:
        logging.error(f"FastAPI connection error: {e}")
    return None


async def get_user_info(user_id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f'{BD_API_URL}/user/{user_id}') as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.error(f"Error while getting user info: {resp.status}")
                    return None
    except aiohttp.ClientError as e:
        logging.error(f"FastAPI connection error: {e}")
        return None


async def get_user_cash(user_id):
    user = await get_user_info(user_id)
    if user:
        return user['cash']
    else:
        return None


async def set_transcription_score(transcription_id: int, score: int):
    try:
        async with aiohttp.ClientSession() as session:
            transcription_data = {
                'score': score
            }
            async with session.put(url=f'{BD_API_URL}/update-transcription-score/{transcription_id}',
                                   params=transcription_data) as resp:
                if resp.status == 200:
                    logging.info(f"Transcription {transcription_id} updated")
                    return True
                else:
                    logging.error(f"Error while updating transcription score: {resp.status}")
                    return False

    except aiohttp.ClientError as e:
        logging.error(f"FastAPI connection error: {e}")
        return False


async def set_user_cash(user_id, cash: int):
    try:
        async with aiohttp.ClientSession() as session:
            transcription_data = {
                'new_cash': cash
            }
            async with session.put(url=f'{BD_API_URL}/update-user-cash/{user_id}',
                                   params=transcription_data) as resp:
                if resp.status == 200:
                    logging.info(f"User {user_id} updated cash")
                    return True
                else:
                    logging.error(f"Error while updating user cash: {resp.status}")
                    return False

    except aiohttp.ClientError as e:
        logging.error(f"FastAPI connection error: {e}")
        return False


async def get_transcription_info(transcription_id: int):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f'{BD_API_URL}/transcription/{transcription_id}') as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.error(f"Error while getting transcription info: {resp.status}")
                    return None
    except aiohttp.ClientError as e:
        logging.error(f"FastAPI connection error: {e}")
        return None
