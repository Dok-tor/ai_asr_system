import asyncio
import json
import logging
import os
import tempfile

from aiogram import Bot, Dispatcher
from aiogram import F, Router
from aiogram.client.session import aiohttp
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, File, InputFile, \
    FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import aiohttp

import bd_connect_module as main_bd
import transcription_connection_module as tranc
import s3_connect_module as s3
from messages_text import start_text, help_text

# from config import API_TOKEN

MAX_MESSAGE_LENGTH = 4000
BD_API_URL = os.getenv('BD_API_URL')
API_TOKEN = os.getenv('TELEGRAM_TOKEN')


bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

SCORE = {
    'bad': 1,
    'normal': 2,
    'best': 3,
}

import hashlib


def generate_short_id(file_id: str) -> str:
    # Генерация короткого хеша
    return hashlib.sha256(file_id.encode()).hexdigest()[:10]  # Берем только первые 10 символов хеша


async def main():
    # dp.include_router(router)
    await dp.start_polling(bot)


class VoiceProcessing(StatesGroup):
    waiting_for_confirmation = State()


main_keyboard = ReplyKeyboardMarkup(keyboard=[
                                    [KeyboardButton(text="/start")],
                                    [KeyboardButton(text="/help"), KeyboardButton(text="/balance")],
                                    ], resize_keyboard=True)


# Обработка команды /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await main_bd.register_user(message.from_user.id)

    photo = FSInputFile("images/cat.png")

    await message.answer_photo(
        photo=photo,
    )

    await message.answer(text=start_text)

    await message.reply(text="Пришлите аудиосообщение:", reply_markup=main_keyboard)


# Обработка получения баланса
@dp.message(Command(commands=['balance']))
async def get_cash(message: Message):
    cash = await main_bd.get_user_cash(message.from_user.id)
    if cash is None:
        await message.reply(text="Произошла ошибка,\nПопробуйте позднее")
    else:
        await message.reply(text=f"На счету у вас:\n{cash:.2f} Монет")


@dp.message(Command(commands=['help']))
async def get_cash(message: Message):
    await message.answer(text=help_text)


# Обработка голосового сообщения
@dp.message(F.voice)
async def handle_voice(message: Message, state: FSMContext):
    voice = message.voice

    # Сохраняем file_id в состоянии пользователя
    short_id = generate_short_id(voice.file_id)
    await state.update_data({short_id: voice.file_id})

    # Создаем inline-кнопку с коротким идентификатором
    confirm_button = InlineKeyboardButton(
        text="Подтвердить обработку",
        callback_data=f"confirm:{short_id}"  # Используем короткий ID
    )

    # Создаем клавиатуру с кнопкой
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[confirm_button]])

    await message.reply("Получено голосовое сообщение. Нажмите кнопку для подтверждения обработки.",
                        reply_markup=inline_kb)

    # Переводим пользователя в состояние ожидания подтверждения
    await state.set_state(VoiceProcessing.waiting_for_confirmation)


# Обработка подтверждения распознавания аудио
@dp.callback_query(F.data.startswith("confirm:"))
async def confirm_audio_processing(callback: CallbackQuery, state: FSMContext):
    short_id = callback.data.split(":")[1]

    error = False

    # Получаем полный file_id по короткому идентификатору
    data = await state.get_data()
    file_id = data.get(short_id)

    if not file_id:
        await callback.message.answer("Ошибка: не удалось найти идентификатор файла.")
        return

    # Не забываем ответить на callback, чтобы убрать значок загрузки
    await callback.answer()

    # Загружаем файл с помощью file_id

    try:
        file = await bot.get_file(file_id)
        file_path = file.file_path
    except Exception as e:
        await callback.message.edit_text(text=
                                         'Возникла ошибка загрузки файла с серверов Telegram\nВозможно файл > 20 Мбайт.',
                                         reply_markup=None)
        return

    await callback.message.edit_text(text='Производится обработка, ожидайте...', reply_markup=None)

    # Работа с временными файлами
    # current_datetime = datetime.now()
    # new_file_name = current_datetime.strftime('%Y_%m_%d_%H_%M_%S')

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg_file:
        await bot.download_file(file_path, temp_ogg_file.name)

        duration = await get_audio_duration(temp_ogg_file.name)
        logging.info(f'duration: {duration}')

        # Преобразуем аудио в подходящий формат (например, wav)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
            os.system(f"ffmpeg -y -i {temp_ogg_file.name} -ar 16000 -ac 1 {temp_wav_file.name}")

    prediction = await tranc.get_prediction(temp_wav_file.name)

    if prediction:

        transcription = await main_bd.add_transcription(callback.from_user.id, int(duration))
        if not transcription:
            logging.error("Transcription is not added to database")

        transcription_id = transcription['data']['transcription_id']

        is_file_download = await s3.send_file_to_s3(temp_wav_file.name, str(transcription_id), prediction)

        get_score_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='❌', callback_data=f'score:bad:{transcription_id}'),
             InlineKeyboardButton(text='👌', callback_data=f'score:normal:{transcription_id}'),
             InlineKeyboardButton(text='✅', callback_data=f'score:best:{transcription_id}'),
             ]])

        await callback.message.edit_text("Аудио успешно распознано")

        await return_prediction(prediction, callback.message, get_score_keyboard)

    else:
        await callback.message.edit_text("К сожалению произошла ошибка.")

    # Удаление временных файлов
    os.remove(temp_ogg_file.name)
    os.remove(temp_wav_file.name)

    data.pop(short_id, None)  # Удаляем ключ, если он существует
    await state.update_data(data)


async def get_audio_duration(filename: str) -> float:
    """Асинхронно получает длительность аудиофайла с помощью ffprobe."""
    process = await asyncio.create_subprocess_exec(
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of', 'json', filename,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(f"Ошибка ffprobe: {stderr.decode()}")
        return 0.0

    info = json.loads(stdout.decode())
    return float(info["format"]["duration"])


async def calculate_balance(balance, duration_seconds):
    k = 0.016 * 5
    if 20 < duration_seconds < 30:
        k *= 1.5
    result = round(k * duration_seconds, 2)
    return balance + result, result


@dp.callback_query(F.data.startswith("score:"))
async def feedback_transcription(callback: CallbackQuery):
    callback_data = callback.data.split(":")
    score = SCORE[callback_data[1]]
    transcription_id = int(callback_data[2])
    logging.info(f"Transcription id: {transcription_id}, score: {score}")
    await callback.answer()

    status = await main_bd.set_transcription_score(transcription_id, score)

    if status:
        await callback.message.edit_reply_markup(reply_markup=None)

    transcription = await main_bd.get_transcription_info(transcription_id)

    if transcription:
        duration = transcription['duration_seconds']
        user_id = callback.from_user.id
        user = await main_bd.get_user_info(user_id)

        if user:
            cash = user['cash']

            new_cash, difference = await calculate_balance(cash, duration)
            result = await main_bd.set_user_cash(user_id, new_cash)
            if result:
                await callback.message.answer(text=f"Спасибо за оценку!\nВам начислено:\n{difference:.2f} Монет")


async def return_prediction(prediction: str, message: Message, keyboard: InlineKeyboardMarkup):
    if len(prediction) > MAX_MESSAGE_LENGTH:
        # Разбиваем текст на строки с учетом слов
        lines = split_text_by_words(prediction, line_length=MAX_MESSAGE_LENGTH)

        # Создаем временный файл и записываем текст в него
        with tempfile.NamedTemporaryFile('w+', suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write('\n'.join(lines))
            temp_file.flush()
            temp_file_path = temp_file.name

            input_file = FSInputFile(temp_file_path, filename="Транскрипция.txt")

            # Отправляем файл пользователю
            await message.reply("Текст слишком большой для демонстрации в виде сообщения.\nТранскрипция в виде файла:")
            await message.reply_document(input_file, reply_markup=keyboard)
    else:
        # Если длина нормальная, отправляем сразу
        await message.reply(f"Транскрипция:\n{prediction}", reply_markup=keyboard)


def split_text_by_words(text: str, line_length: int):
    """Разбивает текст на строки без разрезания слов."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        # Проверяем, поместится ли слово в текущую строку
        if sum(len(w) for w in current_line) + len(current_line) + len(word) <= line_length:
            current_line.append(word)
        else:
            # Если не помещается, добавляем текущую строку в список и начинаем новую
            lines.append(' '.join(current_line))
            current_line = [word]

    # Добавляем последнюю строку, если она не пустая
    if current_line:
        lines.append(' '.join(current_line))

    return lines


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutting down...")
