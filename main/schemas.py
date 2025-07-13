from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class BaseUser(BaseModel):
    tg_uid: int = Field(..., description="uid пользователя telegram")
    habits: Dict[str, int] = Field(
        {}, description="Список привычек с количеством повторений"
    )
    repeat_number: int = Field(
        default=21, description="Требуемое количество повторений привычки"
    )
    date_changed: datetime = Field(
        datetime.now(), description="Время последнего чтения"
    )
    completed: Optional[List] = Field(default=[], description="Выполненные привычки")
    time_zone: int = Field(default=0, description="Код часового пояса")


class GetUser(BaseModel):
    result: bool = True
    user: BaseUser


class UserPatch(BaseModel):
    tg_uid: int = Field(..., description="uid пользователя telegram")
    habits: Dict[str, int] | None = Field(
        None, description="Список привычек с количеством повторений"
    )
    repeat_number: int | None = Field(
        None, description="Требуемое количество повторений привычки"
    )
    date_changed: datetime | None = Field(None, description="Время последнего чтения")
    completed: List | None = Field(None, description="Выполненные привычки")
    time_zone: int | None = Field(None, description="Код часового пояса")


class Result(BaseModel):
    result: bool = True
