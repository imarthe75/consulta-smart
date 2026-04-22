import asyncio
from app.core.database import init_db, get_session
from app.infrastructure.repositories.user_repository import PostgresUserRepository
from app.domain.entities.user import User
from app.core.auth_utils import get_password_hash

async def main():
    await init_db()
    async for session in get_session():
        user_repo = PostgresUserRepository(session)
        
        admin_email = "arquiteturacasmarts@gmail.com"
        admin_pwd = "casmarts_admin_2026"
        
        widget_email = "widget@casmarts.com"
        widget_pwd = "casmarts_widget_2026"

        # Admin
        existing = await user_repo.find_by_email(admin_email)
        if not existing:
            new_admin = User(
                email=admin_email,
                username="AdminArquitectura",
                password_hash=get_password_hash(admin_pwd),
                roles=["admin", "user"]
            )
            await user_repo.create(new_admin)
            print(f"Admin {admin_email} creado.")
        else:
            existing.password_hash = get_password_hash(admin_pwd)
            existing.roles = ["admin", "user"]
            await user_repo.update(existing)
            print(f"Admin {admin_email} actualizado.")

        # Widget
        existing_widget = await user_repo.find_by_email(widget_email)
        if not existing_widget:
            new_widget = User(
                email=widget_email,
                username="UsuarioWidget",
                password_hash=get_password_hash(widget_pwd),
                roles=["user"]
            )
            await user_repo.create(new_widget)
            print(f"Widget user {widget_email} creado.")
        else:
            existing_widget.password_hash = get_password_hash(widget_pwd)
            await user_repo.update(existing_widget)
            print(f"Widget user {widget_email} actualizado.")
            
        await session.commit()
        break 

if __name__ == "__main__":
    asyncio.run(main())
