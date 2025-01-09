from typing import Optional
import asyncpg
from asyncpg.pool import Pool
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    _pool: Optional[Pool] = None
    
    @classmethod
    async def get_pool(cls) -> Pool:
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    database=os.getenv('DB_NAME'),
                    host=os.getenv('DB_HOST'),
                    port=int(os.getenv('DB_PORT', '5432')),
                    min_size=5,
                    max_size=20
                )
            except Exception as e:
                print(f"Failed to create database pool: {str(e)}")
                raise
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def execute(cls, query: str, *args):
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args):
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args):
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.fetchrow(query, *args) 