import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import uvicorn
from asyncpg.exceptions import CannotConnectNowError, UniqueViolationError
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import (
    select,
    update,
)
from sqlalchemy.exc import IntegrityError, ResourceClosedError
from sqlalchemy.ext.asyncio import AsyncSession

from main.schemas import BaseUser, GetUser, UserPatch
from main.models import User
from main.database import AsyncSessionLocal, Base, engine, session

load_dotenv(find_dotenv())

logger.remove()
format_out = "{module} <green>{time:DD-MM-YYYY HH:mm:ss}</green> {level} <level>{message}</level>"
logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
logger.level("WARNING", color="<fg 10,190,200>")


status_code_error = 400
token = os.getenv("token")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    lifespan
    """
    try:
        logger.info("startup")
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield
    except (ConnectionRefusedError, ConnectionError, CannotConnectNowError) as ex:
        logger.error(ex)
        logger.info("Ждем окончания инициализации базы данных")
        time.sleep(10)
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield
    logger.info("Shutdown")
    await session.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


class AuthorizationError(Exception):
    args = ("Ошибка авторизации",)


class UserNotFound(Exception):
    args = ("Пользователь не найден",)


@app.exception_handler(AuthorizationError)
async def custom_api_exception_handler(request: Request, exc: AuthorizationError):
    """
    Функция перехвата ошибок авторизации AuthorizationError
    """
    return JSONResponse(
        status_code=status_code_error,
        content={"result": False},  # noqa: WPS226
    )


@app.exception_handler(ResponseValidationError)
async def validation_response_exception_handler(
    request: Request, exc: ResponseValidationError
):
    """
    Функция перехвата ошибок валидации в Response
    """
    error_body = exc.body
    error = {
        "result": False,
        "error_type": error_body["error_type"],
        "error_message": error_body["error_message"],
    }
    return JSONResponse(error, status_code=status_code_error)


@app.exception_handler(RequestValidationError)
async def validation_request_exception_handler(
    request: Request, exc: RequestValidationError
):
    """
    Функция перехвата ошибок валидации в Request
    """
    error_body = exc.errors()[0]
    error = {
        "result": False,
        "error_type": error_body["type"],
        "error_message": error_body["msg"],
    }
    return JSONResponse(error, status_code=status_code_error)


def errors(ex) -> dict:
    """
    Возвращает словарь с результатом исключения
    :param ex:
    :return:
    """
    return {
        "result": False,
        "error_type": type(ex).__name__,
        "error_message": ex.args[0],
    }


@app.get(
    "/api/user", description="Получить данные пользователя", response_model=GetUser
)
async def get_user(
    tg_uid: int = Header(...),
    authorization_token: str = Header(...),
    session=Depends(get_session),
):
    try:
        if authorization_token != token:
            raise AuthorizationError()
        async with session.begin():
            user = await session.execute(select(User).filter_by(tg_uid=tg_uid))

        user_out = user.scalar_one_or_none()
        if not user_out:
            raise UserNotFound()
        return user_out.to_json()

    except (AuthorizationError, UserNotFound) as ex:
        return errors(ex)


@app.get(
    "/api/get_users",
    description="Получить список всех пользователй с необходимыми атрибутами",
)
async def get_all_users(
    attrib: str = Header(...),
    authorization_token: str = Header(...),
    session=Depends(get_session),
):
    try:
        print(attrib.split())
        columns_name = [column.name for column in User.__table__.columns]
        params_to_stmt = [
            getattr(User, name) if name in columns_name else User.id
            for name in attrib.split()
        ]
        if authorization_token != token:
            raise AuthorizationError()
        async with session.begin():
            users = await session.execute(select(*params_to_stmt))
        users_out = users.mappings().all()
        if not users_out:
            raise UserNotFound()
        print(users_out)
        return {"result": True, "users": users_out}
    except (AuthorizationError, UserNotFound, ResourceClosedError) as ex:
        return errors(ex)


@app.post("/api/make_user", description="Создание пользователя", response_model=GetUser)
async def make_user(
    user: BaseUser, authorization_token: str = Header(...), session=Depends(get_session)
):
    try:
        if authorization_token != token:
            raise AuthorizationError()
        async with session.begin():
            new_user = User(**user.dict())
            # print(user.dict())
            session.add(new_user)
            # await session.commit()
        return new_user.to_json()
    except (AuthorizationError, IntegrityError, UniqueViolationError) as ex:
        return errors(ex)


@app.patch("/api/change_user", description="Изменение данных пользователя")
async def change_user(
    data_in: UserPatch,
    authorization_token: str = Header(...),
    session=Depends(get_session),
):
    """
    Функция изменения данных пользователя по его tg_uid. Изменяются только переданные значения (не None)
    """
    try:
        if authorization_token != token:
            raise AuthorizationError()
        async with session.begin():
            tg_uid = data_in.tg_uid
            if data_in.habits is not None:
                data_in.date_changed = datetime.now()
            data_to_update = data_in.dict(exclude_none=True)
            result = await session.execute(
                update(User)
                .where(User.tg_uid == tg_uid)
                .values(data_to_update)
                .returning(User)
            )
            if result.scalars().one_or_none():
                await session.commit()
            else:
                raise UserNotFound()
            return {"result": True}
    except (AuthorizationError, UserNotFound) as ex:
        return errors(ex)


@app.delete("/api/delete_user", description="Удаление пользователя")
async def delete_user(
    tg_uid: int = Header(...),
    authorization_token: str = Header(...),
    session=Depends(get_session),
):
    try:
        if authorization_token != token:
            raise AuthorizationError()
        async with session.begin():
            user_object = await session.execute(select(User).filter_by(tg_uid=tg_uid))
            user = user_object.scalars().one_or_none()
            if user:
                await session.delete(user)
                await session.commit()
            else:
                raise UserNotFound()
        return {"result": True}
    except (AuthorizationError, UserNotFound) as ex:
        return errors(ex)


if __name__ == "__main__":
    port = 8088
    uvicorn.run("app:app", port=port)
