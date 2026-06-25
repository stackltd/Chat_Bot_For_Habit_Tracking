import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from asyncpg.exceptions import CannotConnectNowError
from fastapi import FastAPI
from fastapi.exceptions import ResponseValidationError
from loguru import logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from main.database import engine, session
from main.exceptions import AuthorizationError, status_code_error
from main.routes import router as router


logger.remove()
format_out = "{module} <green>{time:DD-MM-YYYY HH:mm:ss}</green> {level} <level>{message}</level>"
logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
logger.level("WARNING", color="<fg 10,190,200>")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    lifespan
    """
    try:
        logger.info("startup")
        yield
    except (ConnectionRefusedError, ConnectionError, CannotConnectNowError) as ex:
        logger.error(ex)
        logger.info("Ждем завершения инициализации базы данных")
        time.sleep(10)
        yield
    logger.info("Shutdown")
    await session.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


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


app.include_router(router)

if __name__ == "__main__":
    port = 8088
    uvicorn.run("app:app", port=port)
