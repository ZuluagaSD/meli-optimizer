from urllib.parse import urlparse, urlunparse, quote

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

connect_args: dict = {}
db_url = settings.database_url

if "sqlite" in db_url:
    connect_args["check_same_thread"] = False
elif "pooler.supabase.com" in db_url:
    # Supabase Supavisor: asyncpg chokes on dotted usernames (postgres.ref).
    # Fix: strip the ref from username, pass it via server_settings instead.
    parsed = urlparse(db_url)
    user = parsed.username or ""
    project_ref = ""
    if "." in user:
        base_user, project_ref = user.split(".", 1)
        # Rebuild URL with just "postgres" as username
        netloc = f"{base_user}:{quote(parsed.password or '', safe='')}@{parsed.hostname}:{parsed.port}"
        db_url = urlunparse(parsed._replace(netloc=netloc))
    connect_args["server_settings"] = {
        "options": f"--role=postgres.{project_ref}"
    }

engine = create_async_engine(
    db_url,
    echo=settings.environment == "development",
    connect_args=connect_args,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create all tables (for SQLite dev mode). Skip for PostgreSQL (use migrations)."""
    if "sqlite" in settings.database_url:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
