"""Initial schema with all core tables

Revision ID: 001
Revises:
Create Date: 2026-03-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(50), server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("preferred_language", sa.String(5), server_default="es"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "meli_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("meli_user_id", sa.BigInteger(), unique=True, nullable=False, index=True),
        sa.Column("site_id", sa.String(5), nullable=False),
        sa.Column("nickname", sa.String(255), server_default=""),
        sa.Column("access_token", sa.String(512), nullable=False),
        sa.Column("refresh_token", sa.String(512), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("meli_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meli_accounts.id"), nullable=False, index=True),
        sa.Column("meli_item_id", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("site_id", sa.String(5), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category_id", sa.String(30), server_default=""),
        sa.Column("category_name", sa.String(255), server_default=""),
        sa.Column("price", sa.Float(), server_default="0"),
        sa.Column("currency_id", sa.String(5), server_default="ARS"),
        sa.Column("status", sa.String(20), server_default="active", index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes", postgresql.JSONB(), nullable=True),
        sa.Column("pictures", postgresql.JSONB(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("health_status", sa.String(20), nullable=True),
        sa.Column("attribute_completeness_pct", sa.Float(), server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "optimizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id"), nullable=False, index=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("original_title", sa.String(255), nullable=True),
        sa.Column("suggested_titles", postgresql.JSONB(), nullable=True),
        sa.Column("original_description", sa.Text(), nullable=True),
        sa.Column("suggested_description", sa.Text(), nullable=True),
        sa.Column("suggested_attributes", postgresql.JSONB(), nullable=True),
        sa.Column("model_version", sa.String(50), server_default="claude-sonnet-4-20250514"),
        sa.Column("prompt_version", sa.String(20), server_default="v1"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("optimizations")
    op.drop_table("listings")
    op.drop_table("meli_accounts")
    op.drop_table("users")
    op.drop_table("tenants")
