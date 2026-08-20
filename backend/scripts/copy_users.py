import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_USER = os.environ.get("DB_USER", "consultarpp_user")
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "casmarts-core-db-primary")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_SRC_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/consultarpp_db"
DB_DST_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/consultarpp"

async def copy_users():
    try:
        src_engine = create_async_engine(DB_SRC_URL)
        dst_engine = create_async_engine(DB_DST_URL)

        print("Fetching users from source...")
        async with src_engine.connect() as src_conn:
            result = await src_conn.execute(text("SELECT id, email, username, password_hash, is_active, roles, created_at, updated_at FROM users"))
            users = result.fetchall()
            print(f"Found {len(users)} users.")

            # Hash de respaldo para usuarios sin password_hash en origen
            demo_hash = os.environ["DEMO_PASSWORD_HASH"]

            print("Inserting users into destination...")
            async with dst_engine.begin() as dst_conn:
                for u in users:
                    # use the demo hash if missing
                    pwd_hash = u.password_hash if u.password_hash else demo_hash

                    stmt = text("""
                        INSERT INTO users (id, email, username, password_hash, is_active, roles, created_at, updated_at)
                        VALUES (:id, :email, :username, :password_hash, :is_active, :roles, :created_at, :updated_at)
                        ON CONFLICT (id) DO UPDATE SET
                            password_hash = EXCLUDED.password_hash,
                            roles = EXCLUDED.roles
                    """)
                    await dst_conn.execute(stmt, {
                        "id": u.id, "email": u.email, "username": u.username,
                        "password_hash": pwd_hash, "is_active": u.is_active,
                        "roles": u.roles, "created_at": u.created_at, "updated_at": u.updated_at
                    })
            print("Users copied successfully.")

        await src_engine.dispose()
        await dst_engine.dispose()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(copy_users())
