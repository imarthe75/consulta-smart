import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

DB_URL = "postgresql+asyncpg://consultarpp_user:SuperSecure_ConsultaRPP_2026!@casmarts-core-db-primary:5432/consultarpp_db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def update_password():
    engine = create_async_engine(DB_URL)
    hash_val = pwd_context.hash("demo2026")
    
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET password_hash = :hash WHERE email = 'demo@casmarts.com'"),
            {"hash": hash_val}
        )
    print(f"Password updated to demo2026. Hash: {hash_val}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_password())
