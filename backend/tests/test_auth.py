"""Tests for auth endpoints."""
import pytest
from unittest.mock import AsyncMock, patch


def test_password_hashing():
    from app.services.auth_service import hash_password, verify_password

    hashed = hash_password("test123")
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    from app.services.auth_service import create_jwt, decode_jwt

    token = create_jwt("user-123", "tenant-456")
    payload = decode_jwt(token)
    assert payload["sub"] == "user-123"
    assert payload["tenant_id"] == "tenant-456"


def test_meli_authorize_url():
    from app.services.auth_service import get_meli_authorize_url

    url = get_meli_authorize_url("MLA", "test-state")
    assert "auth.mercadolibre.com.ar" in url
    assert "test-state" in url

    url_br = get_meli_authorize_url("MLB", "state2")
    assert "auth.mercadolivre.com.br" in url_br


def test_meli_authorize_url_invalid_site():
    from app.services.auth_service import get_meli_authorize_url

    with pytest.raises(ValueError, match="Unsupported site"):
        get_meli_authorize_url("INVALID", "state")
