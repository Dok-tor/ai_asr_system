import logging
import os
from datetime import date
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

# Импорт из моего модуля
from db_actions import register_user, update_user, add_transcription, get_user_by_tg_id, get_transcriptions_by_user, \
    get_transactions_by_date_range, set_transcription_score

db_user = os.environ['DB_USER']
db_pass = os.environ['DB_PASSWORD']
db_name = os.environ['DB_NAME']
db_host = os.environ['DB_HOST']

DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}/{db_name}"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем асинхронный движок и фабрику сессий
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Создаем приложение FastAPI
app = FastAPI()


# Dependency для получения сессии
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Pydantic модели для валидации данных
class UserCreateRequest(BaseModel):
    tg_id: int
    cash: float
    role: int


class TranscriptionCreateRequest(BaseModel):
    user_tg_id: int
    score: int
    duration_seconds: int


class UserUpdateRequest(BaseModel):
    cash: Optional[float] = None
    role: Optional[int] = None


# Модель для валидации транзакций
class TransactionResponse(BaseModel):
    id: int
    user_id: int
    datetime: date
    score: int
    filename: str


# Роут для регистрации нового пользователя
@app.post("/register-user/")
async def create_user(request: UserCreateRequest, session: AsyncSession = Depends(get_session)):
    try:
        await register_user(request.tg_id, request.cash, request.role, session)
        return {"status": "success", "message": "User registration initiated"}
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Роут для добавления новой транскрипции
@app.post("/add-transcription/")
async def create_transcription(request: TranscriptionCreateRequest, session: AsyncSession = Depends(get_session)):
    try:
        transcription = await add_transcription(request.user_tg_id, request.score,
                                                request.duration_seconds, session)
        if transcription is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "status": "success",
            "message": "Transcription creation initiated",
            "data": {
                "transcription_id": transcription.pk,
            }
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Роут для обновления данных пользователя
@app.put("/update-user/{tg_id}")
async def update_user_data(tg_id: int, request: UserUpdateRequest, session: AsyncSession = Depends(get_session)):
    try:
        result = await update_user(tg_id, session, request.cash, request.role)
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "success", "message": "User update initiated"}
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Роут для получения информации о пользователе
@app.get("/user/{tg_id}")
async def get_user(tg_id: int, session: AsyncSession = Depends(get_session)):
    try:
        user = await get_user_by_tg_id(tg_id, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"tg_id": user.tg_id, "cash": user.cash, "role": user.role}
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# TODO неверно
# Роут для получения транскрипций пользователя
@app.get("/user/{tg_id}/transcriptions")
async def get_user_transcriptions(tg_id: int, session: AsyncSession = Depends(get_session)):
    try:
        user = await get_user_by_tg_id(tg_id, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        transcriptions = await get_transcriptions_by_user(user.pk, session)
        return [{"filename": t.filename, "score": t.score, "datetime": t.datetime} for t in transcriptions]
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Роут для обновления score у transcription
@app.put("/update-transcription-score/{transcription_id}")
async def change_transcription_score(transcription_id: int, score: int, session: AsyncSession = Depends(get_session)):
    try:
        transcription = await set_transcription_score(transcription_id, score, session)
        if transcription is None:
            raise HTTPException(status_code=404, detail="Transcription not found")
        return {
                "status": "success",
                "message": "Transcription score updated",
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Роут для получения транзакций за определенный промежуток времени
@app.get("/transactions/", response_model=List[TransactionResponse])
async def get_transactions(
        start_date: date,
        end_date: date,
        session: AsyncSession = Depends(get_session)
):
    try:
        transactions = await get_transactions_by_date_range(start_date, end_date, session)
        if not transactions:
            raise HTTPException(status_code=404, detail="No transactions found in the given date range")

        return transactions
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")


# Запуск Uvicorn при запуске скрипта
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
