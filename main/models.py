from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from main.database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_uid = Column(BigInteger, unique=True, nullable=False, index=True)
    habits = Column(JSONB, default=dict())
    completed = Column(JSONB, default=list())
    repeat_number = Column(Integer, default=21)
    date_changed = Column(DateTime, default=datetime.now())
    time_zone = Column(Integer, default=0)

    def __getitem__(self, point):
        return getattr(self, point)

    def to_json(self) -> Dict[str, Any]:
        result_json = {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name != "id"
        }
        return {"user": result_json, "result": True}
