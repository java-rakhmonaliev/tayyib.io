"""
classifier.py — Core classification engine.

Flow:
  1. Parse raw ingredient text into a list of ingredient tokens
  2. For each token, look up in DB (name + aliases)
  3. Collect unknowns → send to AI fallback in one batch
  4. Determine overall verdict based on worst ingredient
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from .models import Ingredient, IngredientStatus


# Priority order: haram > questionable > halal
STATUS_PRIORITY = {
    IngredientStatus.HARAM: 4,
    IngredientStatus.HANAFI_HARAM: 3,
    IngredientStatus.SHAFII_HARAM: 3,
    IngredientStatus.MALIKI_HARAM: 3,
    IngredientStatus.HANBALI_HARAM: 3,
    IngredientStatus.QUESTIONABLE: 2,
    IngredientStatus.HALAL: 1,
}


@dataclass
class IngredientResult:
    original: str
    matched_name: Optional[str]
    status: str
    source: str
    source_url: str
    notes: str
    ai_classified: bool = False


@dataclass
class ClassificationReport:
    overall_status: str
    ingredient_results: list[IngredientResult] = field(default_factory=list)
    unknown_ingredients: list[str] = field(default_factory=list)
    ai_used: bool = False


def parse_ingredients(raw_text: str) -> list[str]:
    """
    Split raw ingredient text into individual tokens.
    Handles: commas, semicolons, parentheses (nested), brackets.
    Example: "Water, Sugar, E471 (Emulsifier), Salt" → ['water', 'sugar', 'e471', 'salt']
    """
    # Remove parenthetical clarifications like "(Emulsifier)" but keep E-codes inside
    text = raw_text.lower()
    # Remove content in parens that doesn't look like an ingredient (just descriptions)
    text = re.sub(r'\([^)]*\)', ' ', text)
    # Split on common delimiters
    tokens = re.split(r'[,;•\n\|/]+', text)
    # Clean each token
    cleaned = []
    for t in tokens:
        t = t.strip().strip('*.-_[]()').strip()
        if t and len(t) >= 2:
            cleaned.append(t)
    return cleaned


def lookup_ingredient(token: str) -> Optional[Ingredient]:
    """
    Look up an ingredient by name or alias (case-insensitive).
    Alias field is a JSON list of strings.
    """
    # Direct name match
    try:
        return Ingredient.objects.get(name__iexact=token)
    except Ingredient.DoesNotExist:
        pass

    # Alias match — check if token appears in any ingredient's aliases list
    # We store aliases as a list of strings in JSONField
    for ingredient in Ingredient.objects.all():
        if any(alias.lower() == token.lower() for alias in ingredient.aliases):
            return ingredient

    return None


def classify(raw_text: str, madhab: str, use_ai: bool = True) -> ClassificationReport:
    """
    Main classification function.
    Returns a ClassificationReport with per-ingredient results and overall verdict.
    """
    from .ai_fallback import classify_unknown_ingredients  # avoid circular import

    tokens = parse_ingredients(raw_text)
    results: list[IngredientResult] = []
    unknowns: list[str] = []

    for token in tokens:
        ingredient = lookup_ingredient(token)
        if ingredient:
            effective_status = ingredient.get_status_for_madhab(madhab)
            results.append(IngredientResult(
                original=token,
                matched_name=ingredient.name,
                status=effective_status,
                source=ingredient.source,
                source_url=ingredient.source_url,
                notes=ingredient.notes,
            ))
        else:
            unknowns.append(token)

    ai_used = False
    if unknowns and use_ai:
        ai_results = classify_unknown_ingredients(unknowns, madhab)
        ai_used = True
        for item in ai_results:
            results.append(IngredientResult(
                original=item['ingredient'],
                matched_name=item['ingredient'],
                status=item['status'],
                source=item['reason'],
                source_url='',
                notes='Classified by AI — verify independently.',
                ai_classified=True,
            ))

    # Determine worst overall status
    if not results:
        overall = IngredientStatus.QUESTIONABLE
    else:
        overall = max(
            results,
            key=lambda r: STATUS_PRIORITY.get(r.status, 0)
        ).status
        # Normalize hanafi/shafii specific statuses to haram for overall display
        if overall in (IngredientStatus.HANAFI_HARAM, IngredientStatus.SHAFII_HARAM):
            overall = IngredientStatus.HARAM

    return ClassificationReport(
        overall_status=overall,
        ingredient_results=results,
        unknown_ingredients=unknowns if not use_ai else [],
        ai_used=ai_used,
    )