from sqlalchemy import select

from main.database import session


class DAO:

    @classmethod
    async def search_by_fields(cls, model, data_dict: dict):
        obj = await session.execute(select(model).filter_by(**data_dict))
        return obj.scalar_one_or_none()

    @classmethod
    async def get_fields(cls, params_to_stmt):
        result = await session.execute(select(*params_to_stmt))
        return result.mappings().all()

    @classmethod
    async def add_object(cls, model, data_dict):
        new_obj = model(**data_dict)
        session.add(new_obj)
        await session.commit()
        return new_obj

    @classmethod
    async def change_object(cls, obj, data_dict):
        for key, value in data_dict.items():
            setattr(obj, key, value)
        session.add(obj)
        await session.commit()

    @classmethod
    async def delete_object(cls, obj):
        await session.delete(obj)
        await session.commit()
