import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date
from models import User, Transcription

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def register_user(tg_id: int, cash: float, role: int, session: AsyncSession):
    try:
        # Проверяем, есть ли уже пользователь с таким tg_id
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        existing_user = result.scalars().first()

        if existing_user:
            logger.info(f"User with tg_id {tg_id} already exists.")
            return existing_user

        # Если пользователя нет, создаем нового
        new_user = User(tg_id=tg_id, cash=cash, role=role)
        session.add(new_user)
        await session.commit()
        logger.info(f"Registered new user with tg_id {tg_id}.")
        return new_user
    except SQLAlchemyError as e:
        logger.error(f"Error registering user: {str(e)}")
        await session.rollback()
        raise


# Добавление информации о транскрипции
async def add_transcription(user_tg_id: int, score: int, duration_seconds: int, session: AsyncSession):
    try:
        # Находим пользователя по tg_id
        result = await session.execute(select(User).filter_by(tg_id=user_tg_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with tg_id {user_tg_id} not found.")
            return None

        # Создаем новую транскрипцию
        new_transcription = Transcription(
            user_id=user.pk,
            # creation_datetime=datetime.now(),
            score=score,
            duration_seconds=duration_seconds,
        )
        session.add(new_transcription)
        await session.commit()
        logger.info(f"Added transcription for user {user_tg_id}.")
        return new_transcription
    except SQLAlchemyError as e:
        logger.error(f"Error adding transcription: {str(e)}")
        await session.rollback()
        raise


# Получение транскрипции по id
async def get_transcription(transcription_id: int, session: AsyncSession):
    try:
        result = await session.execute(select(Transcription).filter_by(pk=transcription_id))
        transcription = result.scalars().first()
        return transcription
    except SQLAlchemyError as e:
        logger.error(f"Error getting transcription: {str(e)}")
        raise


# Обновление cash или role
async def update_user(tg_id: int, session: AsyncSession, cash: Optional[float] = None, role: Optional[int] = None):
    try:
        # Находим пользователя по tg_id
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with tg_id {tg_id} not found.")
            return None

        # Обновляем значения полей
        if cash is not None:
            user.cash = cash
        if role is not None:
            user.role = role

        await session.commit()
        logger.info(f"Updated user {tg_id} with new data (cash={cash}, role={role}).")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error updating user: {str(e)}")
        await session.rollback()
        raise


# Функция для получения пользователя по tg_id
async def get_user_by_tg_id(tg_id: int, session: AsyncSession):
    try:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalars().first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user: {str(e)}")
        raise


# Функция для получения транскрипций пользователя
async def get_transcriptions_by_user(user_id: int, session: AsyncSession):
    try:
        result = await session.execute(select(Transcription).filter_by(user_id=user_id))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching transcriptions: {str(e)}")
        raise


# Функция для обновления score у transcription
async def set_transcription_score(transcription_id: int, score: int, session: AsyncSession):
    try:
        transcription = await get_transcription(transcription_id, session)

        if not transcription:
            logger.error(f"Transcription with tg_id {transcription} not found.")
            return None

        transcription.score = score

        await session.commit()
        logger.info(f"Updated transcription {transcription_id} with new data (score={score}).")
        return transcription
    except SQLAlchemyError as e:
        logger.error(f"Error updating transcription: {str(e)}")
        await session.rollback()
        raise


# Функция для получения транзакций за указанный промежуток времени
async def get_transactions_by_date_range(start_date: date, end_date: date, session: AsyncSession):
    try:
        result = await session.execute(
            select(Transcription).filter(Transcription.datetime >= start_date, Transcription.datetime <= end_date)
        )
        transactions = result.scalars().all()
        return transactions
    except SQLAlchemyError as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise
