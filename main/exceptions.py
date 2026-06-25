from fastapi import HTTPException
from starlette import status

status_code_error = 400


class AuthorizationError(Exception):
    args = ("Ошибка авторизации",)


class UserNotFound(Exception):
    args = ("Пользователь не найден",)


def errors(ex) -> dict:
    return {
        "result": False,
        "error_type": type(ex).__name__,
        "error_message": ex.args[0],
    }


class CredentialsException(HTTPException):
    def __init__(
        self,
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail: str = "Не удалось валидировать учетные данные",
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
