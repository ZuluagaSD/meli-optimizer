import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import bcrypt
import httpx
import jwt
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.meli_account import MeliAccount
from app.models.user import Tenant, User

settings = get_settings()

# Token encryption for MeLi tokens at rest
_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.token_encryption_key
        if not key:
            raise ValueError("TOKEN_ENCRYPTION_KEY not configured")
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


# MeLi OAuth URLs per site
MELI_AUTH_URLS = {
    "MLA": "https://auth.mercadolibre.com.ar",
    "MLB": "https://auth.mercadolivre.com.br",
    "MLM": "https://auth.mercadolibre.com.mx",
}
MELI_API_BASE = "https://api.mercadolibre.com"


def get_meli_authorize_url(site_id: str, state: str) -> str:
    base = MELI_AUTH_URLS.get(site_id)
    if not base:
        raise ValueError(f"Unsupported site: {site_id}")
    params = urlencode({
        "response_type": "code",
        "client_id": settings.meli_app_id,
        "redirect_uri": settings.meli_redirect_uri,
        "state": f"{site_id}:{state}",
    })
    return f"{base}/authorization?{params}"


async def exchange_meli_code(code: str, site_id: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MELI_API_BASE}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": settings.meli_app_id,
                "client_secret": settings.meli_secret_key,
                "code": code,
                "redirect_uri": settings.meli_redirect_uri,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_meli_token(refresh_token: str) -> dict:
    """Refresh an expired MeLi access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MELI_API_BASE}/oauth/token",
            json={
                "grant_type": "refresh_token",
                "client_id": settings.meli_app_id,
                "client_secret": settings.meli_secret_key,
                "refresh_token": refresh_token,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def save_meli_account(
    db: AsyncSession, tenant_id: str, token_data: dict, site_id: str
) -> MeliAccount:
    """Save or update a MeLi account after OAuth."""
    meli_user_id = token_data["user_id"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])

    # Check if account exists
    stmt = select(MeliAccount).where(MeliAccount.meli_user_id == meli_user_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account:
        account.access_token = encrypt_token(token_data["access_token"])
        account.refresh_token = encrypt_token(token_data["refresh_token"])
        account.token_expires_at = expires_at
        account.is_active = True
    else:
        # Fetch user info for nickname
        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                f"{MELI_API_BASE}/users/{meli_user_id}",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            user_info = user_resp.json() if user_resp.status_code == 200 else {}

        account = MeliAccount(
            tenant_id=tenant_id,
            meli_user_id=meli_user_id,
            site_id=site_id,
            nickname=user_info.get("nickname", ""),
            access_token=encrypt_token(token_data["access_token"]),
            refresh_token=encrypt_token(token_data["refresh_token"]),
            token_expires_at=expires_at,
        )
        db.add(account)

    await db.flush()
    return account


async def get_valid_access_token(db: AsyncSession, account: MeliAccount) -> str:
    """Get a valid access token, refreshing if expired."""
    if account.token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        return decrypt_token(account.access_token)

    # Token expired or about to expire — refresh
    refresh_tok = decrypt_token(account.refresh_token)
    token_data = await refresh_meli_token(refresh_tok)

    account.access_token = encrypt_token(token_data["access_token"])
    account.refresh_token = encrypt_token(token_data["refresh_token"])
    account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
    await db.flush()

    return token_data["access_token"]


# Platform auth (JWT)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_jwt(user_id: str, tenant_id: str) -> str:
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


async def register_user(db: AsyncSession, email: str, password: str, name: str) -> User:
    tenant = Tenant(name=name)
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(password),
        name=name,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    stmt = select(User).where(User.email == email, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password_hash):
        return user
    return None
