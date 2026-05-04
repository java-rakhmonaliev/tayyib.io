import logging

import requests

logger = logging.getLogger(__name__)

OFF_WORLD_API = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
OFF_COUNTRY_API = "https://{cc}.openfoodfacts.org/api/v0/product/{barcode}.json"


# ── Public API ────────────────────────────────────────────────────────────────


def fetch_by_barcode(barcode: str, country_code: str = "") -> dict:
    """
    Returns:
        {
            'found': bool,
            'product_name': str,
            'ingredients_text': str,
            'image_url': str,
            'brands': str,
            'source': str,       # 'cache' | 'openfoodfacts' | 'ai_agent'
            'error': str,        # only when found=False
        }

    country_code: ISO 3166-1 alpha-2 (e.g. 'KR', 'DE').
                  Empty string means no country context.
    """
    barcode = barcode.strip()
    country_code = country_code.strip().upper()

    # ── Tier 1: DB cache ──────────────────────────────────────────────────────
    cached = _check_cache(barcode, country_code)
    if cached:
        logger.info(f"[barcode] cache hit barcode={barcode} cc={country_code}")
        return {**cached, "source": "cache"}

    # ── Tier 2: Open Food Facts ───────────────────────────────────────────────
    off_result = _fetch_open_food_facts(barcode, country_code)
    if off_result["found"] and off_result.get("ingredients_text", "").strip():
        logger.info(f"[barcode] OFF hit barcode={barcode} cc={country_code}")
        _save_to_cache(barcode, country_code, off_result, source="openfoodfacts")
        return {**off_result, "source": "openfoodfacts"}

    # ── Nothing found — prompt user to scan label ─────────────────────────────
    return {
        "found": False,
        "error": "product_not_found",
        "message": "Product not in our database.",
        "fallback": "scan_label",
    }


# ── Tier helpers ──────────────────────────────────────────────────────────────


def _check_cache(barcode: str, country_code: str):
    """Returns normalised product dict if cached, else None."""
    from .models import CountryProduct

    try:
        # Try country-specific first, then fall back to global cache entry
        for cc in [country_code, ""]:
            try:
                cp = CountryProduct.objects.get(barcode=barcode, country_code=cc)
                if not cp.ingredients_text:
                    return None  # cached as "not found" — skip
                return {
                    "found": True,
                    "product_name": cp.product_name,
                    "ingredients_text": cp.ingredients_text,
                    "image_url": cp.image_url,
                    "brands": cp.brand,
                }
            except CountryProduct.DoesNotExist:
                continue
    except Exception as e:
        logger.warning(f"[barcode] cache lookup error: {e}")
    return None


def _fetch_open_food_facts(barcode: str, country_code: str) -> dict:
    """Tries country-specific OFF subdomain first, then world."""
    urls = []
    if country_code:
        urls.append(OFF_COUNTRY_API.format(cc=country_code.lower(), barcode=barcode))
    urls.append(OFF_WORLD_API.format(barcode=barcode))

    for url in urls:
        result = _call_off(url)
        if result["found"]:
            return result

    return {"found": False, "error": "Not in Open Food Facts."}


def _call_off(url: str) -> dict:
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "HalalChecker/1.0"})
        data = resp.json()
    except Exception as e:
        return {"found": False, "error": str(e)}

    if data.get("status") != 1:
        return {"found": False, "error": "Product not found."}

    p = data["product"]
    return {
        "found": True,
        "product_name": p.get("product_name", ""),
        "ingredients_text": p.get("ingredients_text", ""),
        "image_url": p.get("image_url", ""),
        "brands": p.get("brands", ""),
    }


# ── Cache writer ──────────────────────────────────────────────────────────────


def _save_to_cache(
    barcode: str,
    country_code: str,
    result: dict,
    source: str,
    low_confidence: bool = False,
):
    from .models import CountryProduct

    try:
        CountryProduct.objects.update_or_create(
            barcode=barcode,
            country_code=country_code,
            defaults={
                "product_name": result.get("product_name", ""),
                "ingredients_text": result.get("ingredients_text", ""),
                "image_url": result.get("image_url", ""),
                "brand": result.get("brands") or result.get("brand", ""),
                "source": source,
                "low_confidence": low_confidence,
            },
        )
        logger.info(
            f"[barcode] saved to cache barcode={barcode} cc={country_code} src={source}"
        )
    except Exception as e:
        logger.error(f"[barcode] cache save failed barcode={barcode}: {e}")
