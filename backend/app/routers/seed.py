"""Seed endpoint for demo purposes — creates sample data."""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import Tenant, User
from app.models.meli_account import MeliAccount
from app.models.listing import Listing
from app.models.optimization import Optimization
from app.services.auth_service import hash_password, create_jwt

router = APIRouter(prefix="/seed", tags=["seed"])

SAMPLE_LISTINGS = [
    {
        "meli_item_id": "MLA1234567890",
        "site_id": "MLA",
        "title": "Celular Samsung Galaxy S24 128gb Negro",
        "category_id": "MLA1055",
        "category_name": "Celulares y Smartphones",
        "price": 899999.0,
        "currency_id": "ARS",
        "status": "active",
        "description": "Samsung Galaxy S24 nuevo en caja sellada. Incluye cargador y auriculares.",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "Samsung"},
            {"id": "MODEL", "name": "Modelo", "value_name": "Galaxy S24"},
            {"id": "INTERNAL_MEMORY", "name": "Memoria interna", "value_name": "128 GB"},
            {"id": "COLOR", "name": "Color", "value_name": "Negro"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=Galaxy+S24", "secure_url": "https://placehold.co/600x600/ffe500/000?text=Galaxy+S24"},
        ],
        "tags": ["good_quality_thumbnail"],
        "health_status": "healthy",
        "attribute_completeness_pct": 85.0,
    },
    {
        "meli_item_id": "MLA9876543210",
        "site_id": "MLA",
        "title": "zapatillas nike air max",
        "category_id": "MLA109027",
        "category_name": "Zapatillas",
        "price": 189999.0,
        "currency_id": "ARS",
        "status": "active",
        "description": "Nike Air Max nuevas. Talle 42. Color blanco.",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "Nike"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=Nike+Air+Max", "secure_url": "https://placehold.co/600x600/ffe500/000?text=Nike+Air+Max"},
        ],
        "tags": ["poor_quality_thumbnail"],
        "health_status": "warning",
        "attribute_completeness_pct": 25.0,
    },
    {
        "meli_item_id": "MLA5555555555",
        "site_id": "MLA",
        "title": "NOTEBOOK HP PAVILION NUEVA!!!",
        "category_id": "MLA1652",
        "category_name": "Notebooks",
        "price": 1299999.0,
        "currency_id": "ARS",
        "status": "active",
        "description": "Notebook HP Pavilion 15. Intel i7. 16GB RAM. SSD 512GB. OFERTA IMPERDIBLE!",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "HP"},
            {"id": "LINE", "name": "Línea", "value_name": "Pavilion"},
            {"id": "PROCESSOR_MODEL", "name": "Modelo del procesador", "value_name": "Intel Core i7"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=HP+Pavilion", "secure_url": "https://placehold.co/600x600/ffe500/000?text=HP+Pavilion"},
        ],
        "tags": ["dragged_bids_and_visits"],
        "health_status": "critical",
        "attribute_completeness_pct": 40.0,
    },
    {
        "meli_item_id": "MLB1111111111",
        "site_id": "MLB",
        "title": "Fone de Ouvido Bluetooth JBL Tune 510BT",
        "category_id": "MLB1051",
        "category_name": "Fones de Ouvido",
        "price": 199.90,
        "currency_id": "BRL",
        "status": "active",
        "description": "Fone JBL Tune 510BT original. Bluetooth 5.0. Bateria de 40h.",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "JBL"},
            {"id": "MODEL", "name": "Modelo", "value_name": "Tune 510BT"},
            {"id": "HEADPHONE_FORMAT", "name": "Formato", "value_name": "On-ear"},
            {"id": "CONNECTIVITY", "name": "Conectividade", "value_name": "Bluetooth"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=JBL+510BT", "secure_url": "https://placehold.co/600x600/ffe500/000?text=JBL+510BT"},
        ],
        "tags": ["good_quality_thumbnail"],
        "health_status": "healthy",
        "attribute_completeness_pct": 90.0,
    },
    {
        "meli_item_id": "MLM2222222222",
        "site_id": "MLM",
        "title": "Silla Gamer Ergonomica Reclinable",
        "category_id": "MLM1144",
        "category_name": "Sillas Gamer",
        "price": 3499.0,
        "currency_id": "MXN",
        "status": "active",
        "description": "Silla gamer con soporte lumbar. Reclinable 180 grados. Base de metal.",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "Genérica"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=Silla+Gamer", "secure_url": "https://placehold.co/600x600/ffe500/000?text=Silla+Gamer"},
        ],
        "tags": [],
        "health_status": "unknown",
        "attribute_completeness_pct": 15.0,
    },
    {
        "meli_item_id": "MLA7777777777",
        "site_id": "MLA",
        "title": "Smart TV 55 Pulgadas 4K Samsung",
        "category_id": "MLA1002",
        "category_name": "Televisores",
        "price": 749999.0,
        "currency_id": "ARS",
        "status": "paused",
        "description": "Smart TV Samsung 55 pulgadas. 4K UHD. HDR10+.",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "Samsung"},
            {"id": "SCREEN_SIZE", "name": "Tamaño de pantalla", "value_name": "55 \""},
            {"id": "DISPLAY_RESOLUTION_TYPE", "name": "Resolución", "value_name": "4K Ultra HD"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=Samsung+TV", "secure_url": "https://placehold.co/600x600/ffe500/000?text=Samsung+TV"},
        ],
        "tags": ["good_quality_thumbnail"],
        "health_status": "healthy",
        "attribute_completeness_pct": 70.0,
    },
    {
        "meli_item_id": "MLB3333333333",
        "site_id": "MLB",
        "title": "kit ferramentas manuais completo",
        "category_id": "MLB278169",
        "category_name": "Kits de Ferramentas",
        "price": 89.90,
        "currency_id": "BRL",
        "status": "active",
        "description": "Kit completo com 120 peças. Maleta organizadora incluída.",
        "attributes": [],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=Ferramentas", "secure_url": "https://placehold.co/600x600/ffe500/000?text=Ferramentas"},
        ],
        "tags": ["poor_quality_picture"],
        "health_status": "warning",
        "attribute_completeness_pct": 0.0,
    },
    {
        "meli_item_id": "MLA8888888888",
        "site_id": "MLA",
        "title": "Auriculares Inalambricos Bluetooth Deportivos",
        "category_id": "MLA1051",
        "category_name": "Auriculares",
        "price": 45999.0,
        "currency_id": "ARS",
        "status": "active",
        "description": "Auriculares bluetooth deportivos. Resistentes al agua IPX5.",
        "attributes": [
            {"id": "BRAND", "name": "Marca", "value_name": "Genérica"},
            {"id": "CONNECTIVITY", "name": "Conectividad", "value_name": "Bluetooth"},
        ],
        "pictures": [
            {"url": "https://placehold.co/600x600/ffe500/000?text=Auriculares", "secure_url": "https://placehold.co/600x600/ffe500/000?text=Auriculares"},
        ],
        "tags": [],
        "health_status": "unknown",
        "attribute_completeness_pct": 35.0,
    },
]


@router.post("")
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """Create demo user, MeLi accounts, and sample listings."""
    # Check if already seeded
    existing = await db.execute(select(User).where(User.email == "demo@melioptimizer.com"))
    if existing.scalar_one_or_none():
        user = (await db.execute(select(User).where(User.email == "demo@melioptimizer.com"))).scalar_one()
        token = create_jwt(str(user.id), str(user.tenant_id))
        return {"message": "Already seeded", "token": token, "email": "demo@melioptimizer.com", "password": "demo1234"}

    # Create tenant + user
    tenant = Tenant(name="Demo Seller")
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email="demo@melioptimizer.com",
        password_hash=hash_password("demo1234"),
        name="Demo Seller",
        preferred_language="es",
    )
    db.add(user)
    await db.flush()

    # Create MeLi accounts (fake — one per market)
    accounts = {}
    for site_id, meli_uid, nickname in [
        ("MLA", 123456789, "DEMO_SELLER_AR"),
        ("MLB", 987654321, "DEMO_SELLER_BR"),
        ("MLM", 555555555, "DEMO_SELLER_MX"),
    ]:
        acc = MeliAccount(
            tenant_id=tenant.id,
            meli_user_id=meli_uid,
            site_id=site_id,
            nickname=nickname,
            access_token="demo_token",
            refresh_token="demo_refresh",
            token_expires_at=datetime.now(timezone.utc) + timedelta(hours=6),
        )
        db.add(acc)
        await db.flush()
        accounts[site_id] = acc

    # Create sample listings
    for item in SAMPLE_LISTINGS:
        site_id = item["site_id"]
        account = accounts[site_id]
        listing = Listing(
            meli_account_id=account.id,
            meli_item_id=item["meli_item_id"],
            site_id=site_id,
            title=item["title"],
            category_id=item["category_id"],
            category_name=item["category_name"],
            price=item["price"],
            currency_id=item["currency_id"],
            status=item["status"],
            description=item["description"],
            attributes=item["attributes"],
            pictures=item["pictures"],
            tags=item["tags"],
            health_status=item["health_status"],
            attribute_completeness_pct=item["attribute_completeness_pct"],
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(listing)

    await db.flush()

    token = create_jwt(str(user.id), str(user.tenant_id))
    return {
        "message": "Demo data created",
        "token": token,
        "email": "demo@melioptimizer.com",
        "password": "demo1234",
    }
