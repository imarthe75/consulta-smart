import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

DB_USER = os.environ.get("DB_USER", "consultarpp_user")
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "casmarts-core-db-primary")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/consultarpp_db"
TARGET_EMAIL = os.environ.get("TARGET_EMAIL", "demo@casmarts.com")
NEW_PASSWORD = os.environ["NEW_PASSWORD"]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def update_password():
    engine = create_async_engine(DB_URL)
    hash_val = pwd_context.hash(NEW_PASSWORD)

    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET password_hash = :hash WHERE email = :email"),
            {"hash": hash_val, "email": TARGET_EMAIL}
        )
    print(f"Password updated for {TARGET_EMAIL}.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_password())
