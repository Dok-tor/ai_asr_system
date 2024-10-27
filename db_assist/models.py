from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Таблица пользователей
class User(Base):
    __tablename__ = 'users'

    pk = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    registration_datetime = Column(DateTime, default=func.now(), nullable=False)
    cash = Column(Numeric(10, 2), nullable=False)  # Используем Numeric
    role = Column(Integer, nullable=False)

    # Связь с таблицей Transcriptions
    transcriptions = relationship('Transcription', back_populates='user')


# Таблица транскрипций
class Transcription(Base):
    __tablename__ = 'transcriptions'

    pk = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)
    creation_datetime = Column(DateTime, default=func.now(), nullable=False)
    score = Column(Integer, nullable=False)
    # filename = Column(String, nullable=False)
    duration_seconds = Column(Integer, nullable=False)

    # Связь с таблицей Users
    user = relationship('User', back_populates='transcriptions')


class Transaction(Base):
    __tablename__ = 'transactions'

    pk = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)
    date_of_transaction = Column(DateTime, default=func.now(), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
