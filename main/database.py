import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

load_dotenv(find_dotenv())

login = os.getenv("login")
password = os.getenv("password")

# для подключения к контейнеру с postgres, но через приложение снаружи
# DATABASE_URL = f"postgresql+asyncpg://{login}:{password}@localhost:5432/chat_bot"

# использовать для сборки контейнера с приложением fastapi
DATABASE_URL = f"postgresql+asyncpg://{login}:{password}@postgres:5432/chat_bot"


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
session = AsyncSessionLocal()
Base = declarative_base()
