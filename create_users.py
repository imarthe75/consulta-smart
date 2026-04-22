import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.core.security import get_password_hash

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    admin_email = "arquiteturacasmarts@gmail.com"
    admin_pwd = "casmarts_admin_2026"
    admin_hash = get_password_hash(admin_pwd)
    
    widget_email = "widget@casmarts.com"
    widget_pwd = "casmarts_widget_2026"
    widget_hash = get_password_hash(widget_pwd)

    async with async_session() as session:
        await session.execute(text(
            "INSERT INTO users (email, username, hashed_password, is_active, role) VALUES (:email, :username, :hash, true, 'admin') ON CONFLICT (email) DO UPDATE SET hashed_password = :hash, role = 'admin'"
        ), {"email": admin_email, "username": "AdminArquitectura", "hash": admin_hash})
        
        await session.execute(text(
            "INSERT INTO users (email, username, hashed_password, is_active, role) VALUES (:email, :username, :hash, true, 'user') ON CONFLICT (email) DO UPDATE SET hashed_password = :hash"
        ), {"email": widget_email, "username": "UsuarioWidget", "hash": widget_hash})
        
        await session.commit()
    print("Usuarios creados exitosamente")

asyncio.run(main())
