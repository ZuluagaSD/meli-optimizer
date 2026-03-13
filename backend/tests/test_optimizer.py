"""Tests for optimizer prompt building."""


def test_get_language():
    from app.services.optimizer import _get_language

    assert _get_language("MLA") == "es"
    assert _get_language("MLB") == "pt"
    assert _get_language("MLM") == "es"


def test_format_attributes():
    from app.services.optimizer import _format_attributes

    assert _format_attributes([]) == "(ninguno / nenhum)"

    attrs = [
        {"name": "Brand", "value_name": "Samsung"},
        {"name": "Model", "value_name": "Galaxy S24"},
    ]
    result = _format_attributes(attrs)
    assert "Brand: Samsung" in result
    assert "Model: Galaxy S24" in result


def test_format_attributes_limits():
    from app.services.optimizer import _format_attributes

    # Should limit to 20 attributes
    attrs = [{"name": f"Attr {i}", "value_name": f"Val {i}"} for i in range(30)]
    result = _format_attributes(attrs)
    lines = result.strip().split("\n")
    assert len(lines) == 20
