#!/usr/bin/env python3
import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    system_user_id = "019d73a6-d320-7c49-bee7-b19f368473ec"
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            text("SELECT id FROM users WHERE id = :id"),
            {"id": system_user_id}
        )
        if result.fetchone():
            print(f"✅ System user {system_user_id} already exists")
            return

        # Create system user
        print(f"👤 Creating system user {system_user_id}...")
        await session.execute(
            text("""
                INSERT INTO users (id, email, username, is_active, roles, created_at, updated_at)
                VALUES (:id, :email, :username, :is_active, :roles, NOW(), NOW())
            """),
            {
                "id": system_user_id,
                "email": "system@casmarts.core",
                "username": "system_admin",
                "is_active": True,
                "roles": '["admin", "system"]'
            }
        )
        await session.commit()
        print("✅ System user created successfully")

if __name__ == "__main__":
    asyncio.run(main())
