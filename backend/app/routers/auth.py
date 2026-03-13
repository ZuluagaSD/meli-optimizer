import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.meli_account import MeliAccount
from app.models.user import User
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


# ----- Schemas -----

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeliAccountResponse(BaseModel):
    id: str
    meli_user_id: int
    site_id: str
    nickname: str
    is_active: bool


# ----- Dependency: get current user -----

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth_header[7:]
    try:
        payload = auth_service.decode_jwt(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ----- Platform Auth -----

@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check existing
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await auth_service.register_user(db, body.email, body.password, body.name)
    token = auth_service.create_jwt(str(user.id), str(user.tenant_id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth_service.create_jwt(str(user.id), str(user.tenant_id))
    return TokenResponse(access_token=token)


# ----- MeLi OAuth -----

@router.get("/meli/authorize")
async def meli_authorize(
    site_id: str = Query(..., regex="^(MLA|MLB|MLM)$"),
    user: User = Depends(get_current_user),
):
    state = str(user.tenant_id)
    url = auth_service.get_meli_authorize_url(site_id, state)
    return RedirectResponse(url)


@router.get("/meli/callback")
async def meli_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # state format: "SITE_ID:tenant_id"
    parts = state.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid state")
    site_id, tenant_id = parts

    try:
        token_data = await auth_service.exchange_meli_code(code, site_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {e}")

    await auth_service.save_meli_account(db, tenant_id, token_data, site_id)

    # Redirect to frontend dashboard
    return RedirectResponse("http://localhost:3000/dashboard?meli_connected=true")


@router.post("/meli/disconnect/{account_id}")
async def meli_disconnect(
    account_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MeliAccount).where(
        MeliAccount.id == account_id,
        MeliAccount.tenant_id == user.tenant_id,
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.is_active = False
    return {"status": "disconnected"}


@router.get("/meli/accounts", response_model=list[MeliAccountResponse])
async def list_meli_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MeliAccount).where(
        MeliAccount.tenant_id == user.tenant_id,
        MeliAccount.is_active == True,
    )
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [
        MeliAccountResponse(
            id=str(a.id),
            meli_user_id=a.meli_user_id,
            site_id=a.site_id,
            nickname=a.nickname,
            is_active=a.is_active,
        )
        for a in accounts
    ]
