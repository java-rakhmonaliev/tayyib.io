"""
barcode.py — Fetch product info from Open Food Facts by barcode.
Free API, no key required.
"""

import requests

OFF_API = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"


def fetch_by_barcode(barcode: str) -> dict:
    """
    Returns dict with:
      - product_name: str
      - ingredients_text: str  (raw ingredient list)
      - image_url: str
      - found: bool
    """
    try:
        resp = requests.get(
            OFF_API.format(barcode=barcode.strip()),
            timeout=8,
            headers={"User-Agent": "HalalChecker/1.0"}
        )
        data = resp.json()
    except Exception as e:
        return {"found": False, "error": str(e)}

    if data.get("status") != 1:
        return {"found": False, "error": "Product not found in Open Food Facts database."}

    product = data["product"]
    return {
        "found": True,
        "product_name": product.get("product_name", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "image_url": product.get("image_url", ""),
        "brands": product.get("brands", ""),
    }