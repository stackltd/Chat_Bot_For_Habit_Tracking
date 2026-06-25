from asyncpg.exceptions import UniqueViolationError
from fastapi import Header, APIRouter

from sqlalchemy.exc import ResourceClosedError

from main.exceptions import AuthorizationError, UserNotFound, errors
from main.schemas import BaseUser, GetUser, UserPatch
from main.services import ApiService


router = APIRouter(prefix="/api", tags=["Bot"])


@router.get("/user", description="Получить данные пользователя", response_model=GetUser)
async def get_user(tg_uid: int = Header(...), authorization_token: str = Header(...)):
    try:
        return await ApiService.get_user(authorization_token, tg_uid)
    except (AuthorizationError, UserNotFound) as ex:
        return errors(ex)


@router.get(
    "/get_users",
    description="Получить список всех пользователй с необходимыми атрибутами",
)
async def get_all_users(
    attrib: str = Header(...),
    authorization_token: str = Header(...),
):
    try:
        users_out = await ApiService.get_users(authorization_token, attrib)
    except (AuthorizationError, UserNotFound, ResourceClosedError) as ex:
        return errors(ex)
    return {"result": True, "users": users_out}


@router.post("/make_user", description="Создание пользователя", response_model=GetUser)
async def make_user(user: BaseUser, authorization_token: str = Header(...)):
    try:
        return (await ApiService.make_user(authorization_token, user)).to_json()
    except (AuthorizationError, UniqueViolationError) as ex:
        return errors(ex)


@router.patch("/change_user", description="Изменение данных пользователя")
async def change_user(data_in: UserPatch, authorization_token: str = Header(...)):
    """Функция изменения данных пользователя по его tg_uid. Изменяются только переданные значения (не None)"""
    try:
        await ApiService.change_user(data_in, authorization_token)
    except (AuthorizationError, UserNotFound) as ex:
        return errors(ex)
    return {"result": True}


@router.delete("/delete_user", description="Удаление пользователя")
async def delete_user(
    tg_uid: int = Header(...),
    authorization_token: str = Header(...),
):
    try:
        await ApiService.delete_user(authorization_token, tg_uid)
    except (AuthorizationError, UserNotFound) as ex:
        return errors(ex)
    return {"result": True}
