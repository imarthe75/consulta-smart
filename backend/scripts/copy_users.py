import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_SRC_URL = "postgresql+asyncpg://consultarpp_user:SuperSecure_ConsultaRPP_2026!@casmarts-core-db-primary:5432/consultarpp_db"
DB_DST_URL = "postgresql+asyncpg://consultarpp_user:SuperSecure_ConsultaRPP_2026!@casmarts-core-db-primary:5432/consultarpp"

async def copy_users():
    try:
        src_engine = create_async_engine(DB_SRC_URL)
        dst_engine = create_async_engine(DB_DST_URL)
        
        print("Fetching users from source...")
        async with src_engine.connect() as src_conn:
            result = await src_conn.execute(text("SELECT id, email, username, password_hash, is_active, roles, created_at, updated_at FROM users"))
            users = result.fetchall()
            print(f"Found {len(users)} users.")
            
            # Hash for demo@casmarts.com
            demo_hash = "$2b$12$tsHr3Rhc.4Nx17ZyLFXQGODX6LmHi5pwCcbRJYLy75VySDf2pzhw6"
            
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
