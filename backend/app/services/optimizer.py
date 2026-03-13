import json
import hashlib
from typing import Any

import anthropic

from app.config import get_settings
from app.models.listing import Listing

settings = get_settings()

# In-memory cache (use Redis in production)
_cache: dict[str, str] = {}


# ----- Prompt Templates by Market -----

SYSTEM_PROMPTS = {
    "MLA": """Eres un experto en optimización de publicaciones de Mercado Libre Argentina (MLA).
Conocés las mejores prácticas para títulos, descripciones y atributos en el mercado argentino.
Reglas de títulos MeLi:
- Formato: Producto + Marca + Modelo + Especificaciones clave
- Máximo 60 caracteres
- No usar lenguaje promocional (sin "OFERTA", "ENVÍO GRATIS", etc.)
- No usar MAYÚSCULAS completas
- No usar signos de exclamación ni caracteres especiales innecesarios
- Usar terminología local argentina""",

    "MLB": """Você é um especialista em otimização de anúncios do Mercado Livre Brasil (MLB).
Conhece as melhores práticas para títulos, descrições e atributos no mercado brasileiro.
Regras de títulos MeLi:
- Formato: Produto + Marca + Modelo + Especificações-chave
- Máximo 60 caracteres
- Não usar linguagem promocional (sem "OFERTA", "FRETE GRÁTIS", etc.)
- Não usar MAIÚSCULAS completas
- Não usar sinais de exclamação ou caracteres especiais desnecessários
- Usar terminologia local brasileira""",

    "MLM": """Eres un experto en optimización de publicaciones de Mercado Libre México (MLM).
Conoces las mejores prácticas para títulos, descripciones y atributos en el mercado mexicano.
Reglas de títulos MeLi:
- Formato: Producto + Marca + Modelo + Especificaciones clave
- Máximo 60 caracteres
- No usar lenguaje promocional (sin "OFERTA", "ENVÍO GRATIS", etc.)
- No usar MAYÚSCULAS completas
- No usar signos de exclamación ni caracteres especiales innecesarios
- Usar terminología local mexicana""",
}

TITLE_USER_PROMPT = {
    "es": """Analiza esta publicación de Mercado Libre y genera 3 variantes de título optimizadas.

**Publicación actual:**
- Título: {title}
- Categoría: {category_name}
- Precio: {price} {currency}

**Atributos del producto:**
{attributes}

**Títulos de competidores (top 5):**
{competitor_titles}

**Atributos requeridos por la categoría:**
{required_attributes}

Genera exactamente 3 variantes de título optimizadas. Cada una debe:
1. Seguir el formato: Producto + Marca + Modelo + Specs clave
2. Tener máximo 60 caracteres
3. Incluir las palabras clave más relevantes para SEO
4. No repetir información innecesaria

Responde SOLO con JSON válido en este formato:
{{
  "variants": [
    {{"title": "...", "reasoning": "..."}},
    {{"title": "...", "reasoning": "..."}},
    {{"title": "...", "reasoning": "..."}}
  ]
}}""",

    "pt": """Analise este anúncio do Mercado Livre e gere 3 variantes de título otimizadas.

**Anúncio atual:**
- Título: {title}
- Categoria: {category_name}
- Preço: {price} {currency}

**Atributos do produto:**
{attributes}

**Títulos de concorrentes (top 5):**
{competitor_titles}

**Atributos exigidos pela categoria:**
{required_attributes}

Gere exatamente 3 variantes de título otimizadas. Cada uma deve:
1. Seguir o formato: Produto + Marca + Modelo + Specs principais
2. Ter no máximo 60 caracteres
3. Incluir as palavras-chave mais relevantes para SEO
4. Não repetir informações desnecessárias

Responda APENAS com JSON válido neste formato:
{{
  "variants": [
    {{"title": "...", "reasoning": "..."}},
    {{"title": "...", "reasoning": "..."}},
    {{"title": "...", "reasoning": "..."}}
  ]
}}""",
}

ATTRIBUTE_USER_PROMPT = {
    "es": """Analiza los atributos faltantes de esta publicación de Mercado Libre y sugiere valores.

**Publicación:**
- Título: {title}
- Categoría: {category_name}

**Atributos actuales:**
{current_attributes}

**Atributos requeridos faltantes:**
{missing_attributes}

Para cada atributo faltante, sugiere el valor más probable basándote en el título y los atributos existentes.
Si un atributo tiene valores permitidos, elige de esa lista.

Responde SOLO con JSON válido:
{{
  "suggestions": [
    {{"attribute_id": "...", "attribute_name": "...", "suggested_value": "...", "confidence": "high|medium|low", "reasoning": "..."}}
  ]
}}""",

    "pt": """Analise os atributos faltantes deste anúncio do Mercado Livre e sugira valores.

**Anúncio:**
- Título: {title}
- Categoria: {category_name}

**Atributos atuais:**
{current_attributes}

**Atributos obrigatórios faltantes:**
{missing_attributes}

Para cada atributo faltante, sugira o valor mais provável com base no título e atributos existentes.
Se um atributo tiver valores permitidos, escolha dessa lista.

Responda APENAS com JSON válido:
{{
  "suggestions": [
    {{"attribute_id": "...", "attribute_name": "...", "suggested_value": "...", "confidence": "high|medium|low", "reasoning": "..."}}
  ]
}}""",
}


def _get_language(site_id: str) -> str:
    return "pt" if site_id == "MLB" else "es"


def _format_attributes(attrs: list[dict]) -> str:
    if not attrs:
        return "(ninguno / nenhum)"
    lines = []
    for a in attrs[:20]:  # limit to avoid token bloat
        name = a.get("name", a.get("id", "?"))
        value = a.get("value_name", "N/A")
        lines.append(f"- {name}: {value}")
    return "\n".join(lines)


def _cache_key(listing_id: str, opt_type: str) -> str:
    return f"opt:{listing_id}:{opt_type}"


async def optimize_title(
    listing: Listing,
    competitor_titles: list[str],
    category_attributes: list[dict],
) -> dict:
    """Generate 3 optimized title variants using Claude API."""
    site_id = listing.site_id
    lang = _get_language(site_id)

    # Check cache
    cache_key = _cache_key(str(listing.id), "title")
    cached = _cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Build required attributes string
    required = [a for a in category_attributes if a.get("tags", {}).get("required")]
    required_str = _format_attributes(required) if required else "(none)"

    # Build competitor titles string
    comp_str = "\n".join(f"- {t}" for t in competitor_titles[:5]) if competitor_titles else "(no competitors found)"

    # Format current attributes
    attrs_str = _format_attributes(listing.attributes or [])

    user_prompt = TITLE_USER_PROMPT[lang].format(
        title=listing.title,
        category_name=listing.category_name or listing.category_id,
        price=listing.price,
        currency=listing.currency_id,
        attributes=attrs_str,
        competitor_titles=comp_str,
        required_attributes=required_str,
    )

    system_prompt = SYSTEM_PROMPTS.get(site_id, SYSTEM_PROMPTS["MLA"])

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    # Parse JSON from response
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
        else:
            result = {"variants": [], "error": "Failed to parse response"}

    # Cache in memory
    _cache[cache_key] = json.dumps(result)

    return result


async def suggest_attributes(
    listing: Listing,
    category_attributes: list[dict],
) -> dict:
    """Suggest values for missing required attributes."""
    site_id = listing.site_id
    lang = _get_language(site_id)

    # Check cache
    cache_key = _cache_key(str(listing.id), "attributes")
    cached = _cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Find missing required attributes
    current_ids = {a.get("id") for a in (listing.attributes or []) if a.get("value_name")}
    missing = []
    for attr in category_attributes:
        is_required = attr.get("tags", {}).get("required", False)
        if is_required and attr["id"] not in current_ids:
            allowed = attr.get("values", [])
            allowed_str = ", ".join(v["name"] for v in allowed[:10]) if allowed else "free text"
            missing.append(f"- {attr['name']} (id: {attr['id']}, allowed: {allowed_str})")

    if not missing:
        return {"suggestions": []}

    current_str = _format_attributes(listing.attributes or [])
    missing_str = "\n".join(missing)

    user_prompt = ATTRIBUTE_USER_PROMPT[lang].format(
        title=listing.title,
        category_name=listing.category_name or listing.category_id,
        current_attributes=current_str,
        missing_attributes=missing_str,
    )

    system_prompt = SYSTEM_PROMPTS.get(site_id, SYSTEM_PROMPTS["MLA"])

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
        else:
            result = {"suggestions": [], "error": "Failed to parse response"}

    _cache[cache_key] = json.dumps(result)

    return result
