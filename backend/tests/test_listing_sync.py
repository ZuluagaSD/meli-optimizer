"""Tests for listing sync logic."""


def test_calculate_attribute_completeness():
    from app.services.listing_sync import _calculate_attribute_completeness

    category_attrs = [
        {"id": "BRAND", "tags": {"required": True}},
        {"id": "MODEL", "tags": {"required": True}},
        {"id": "COLOR", "tags": {"required": True}},
        {"id": "WEIGHT", "tags": {}},
    ]

    # All required filled
    item_attrs = [
        {"id": "BRAND", "value_name": "Samsung"},
        {"id": "MODEL", "value_name": "S24"},
        {"id": "COLOR", "value_name": "Black"},
    ]
    assert _calculate_attribute_completeness(item_attrs, category_attrs) == 100.0

    # Only 1 of 3 required
    item_attrs_partial = [
        {"id": "BRAND", "value_name": "Samsung"},
    ]
    pct = _calculate_attribute_completeness(item_attrs_partial, category_attrs)
    assert pct == pytest.approx(33.3, abs=0.1)

    # No required attrs in category
    assert _calculate_attribute_completeness([], [{"id": "X", "tags": {}}]) == 100.0


def test_detect_health_status():
    from app.services.listing_sync import _detect_health_status

    assert _detect_health_status(None) == "unknown"
    assert _detect_health_status([]) == "unknown"
    assert _detect_health_status(["good_quality_thumbnail"]) == "healthy"
    assert _detect_health_status(["poor_quality_thumbnail"]) == "warning"
    assert _detect_health_status(["dragged_bids_and_visits"]) == "critical"


import pytest
