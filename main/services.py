import os
from datetime import datetime

from starlette import status

from main.dao import DAO
from main.exceptions import AuthorizationError, UserNotFound, CredentialsException
from main.models import User

token = os.getenv("token")


class ApiService:

    @classmethod
    async def get_user(cls, authorization_token, tg_uid):
        if authorization_token != token:
            raise AuthorizationError()
        user_out = await DAO.search_by_fields(User, dict(tg_uid=tg_uid))
        if not user_out:
            raise UserNotFound()
        return user_out.to_json()

    @classmethod
    async def get_users(cls, authorization_token, attrib):
        columns_name = [column.name for column in User.__table__.columns]
        params_to_stmt = [
            getattr(User, name) if name in columns_name else User.id
            for name in attrib.split()
        ]
        if authorization_token != token:
            raise AuthorizationError()
        users_out = await DAO.get_fields(params_to_stmt)
        if not users_out:
            raise UserNotFound()
        return users_out

    @classmethod
    async def make_user(cls, authorization_token, user):
        if authorization_token != token:
            raise AuthorizationError()

        user_exist = await DAO.search_by_fields(User, dict(tg_uid=user.tg_uid))
        if user_exist:
            message = f"Ошибка. Пользователь {user.tg_uid} уже существует"
            raise CredentialsException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            )

        new_user = await DAO.add_object(User, user.dict())
        return new_user

    @classmethod
    async def change_user(cls, data_in, authorization_token):
        if authorization_token != token:
            raise AuthorizationError()
        user_exist = await DAO.search_by_fields(User, dict(tg_uid=data_in.tg_uid))
        if not user_exist:
            raise UserNotFound
        if data_in.habits is not None:
            data_in.date_changed = datetime.now()
        data_to_update = data_in.dict(exclude_none=True)
        await DAO.change_object(user_exist, data_to_update)

    @classmethod
    async def delete_user(cls, authorization_token, tg_uid):
        if authorization_token != token:
            raise AuthorizationError()
        user_exist = await DAO.search_by_fields(User, dict(tg_uid=tg_uid))
        if not user_exist:
            raise UserNotFound
        await DAO.delete_object(user_exist)
