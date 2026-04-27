import json
from groq import Groq
from django.conf import settings

MADHAB_RULES = {
    'hanafi': """HANAFI RULES (strictest on seafood):
- Only scaled bony fish are halal
- Shrimp, prawns, crab, lobster, squid, octopus, shellfish, mussels, oysters, clams, scallops = HARAM
- Shark = HARAM
- Horse = HARAM
- Wine vinegar = HARAM
- All pork derivatives = HARAM""",

    'maliki': """MALIKI RULES:
- All fish are halal
- Shrimp, prawns = HALAL
- Crab, lobster, shellfish = HARAM
- Shark = HALAL
- Horse = HALAL
- Wine vinegar = HALAL
- All pork derivatives = HARAM""",

    'shafii': """SHAFI'I RULES (most permissive on seafood):
- All seafood is halal without exception
- Shrimp, prawns, crab, lobster, shellfish, squid, octopus = HALAL
- Shark = HALAL
- Horse = HALAL
- Wine vinegar = HALAL
- All pork derivatives = HARAM""",

    'hanbali': """HANBALI RULES:
- All fish are halal
- Shrimp, prawns = HALAL
- Crab, lobster = HALAL
- Shark = HALAL
- Horse = HALAL
- Wine vinegar = HARAM
- All pork derivatives = HARAM""",
}

SYSTEM_PROMPT_BASE = """You are a strict Islamic halal food auditor with deep knowledge of all four major schools of thought (Hanafi, Maliki, Shafi'i, Hanbali).

Given a list of food ingredients, classify each as:
- halal: clearly permissible
- haram: clearly forbidden
- questionable: uncertain, source unknown, or debated

UNIVERSAL HARAM (all madhabs):
- Pork, lard, pig-derived anything
- Blood and blood products
- Alcohol as main ingredient (wine, beer, spirits)
- Carmine / E120 / cochineal (insect dye)
- L-Cysteine (E920) from pork or human hair

AMBIGUOUS — DEFAULT TO QUESTIONABLE IF SOURCE UNKNOWN:
- Gelatin: pork source = haram. Fish/halal beef = halal. Unspecified = questionable.
- Glycerin: vegetable = halal. Animal/unspecified = questionable.
- Mono and diglycerides (E471): unspecified = questionable.
- Natural flavour/flavoring: always questionable.
- Rennet: animal unspecified = questionable.
- Whey, casein: questionable.
- Lecithin: soy/sunflower = halal. Unspecified = questionable.

ALWAYS HALAL: water, salt, sugar, all fruits/vegetables/grains/legumes/nuts/seeds, plant-based oils, eggs, honey, spices, herbs, mineral/synthetic E-numbers.

GOLDEN RULE: When in doubt, mark questionable. A false halal is worse than a false haram.

Respond ONLY with a valid JSON array. No text outside JSON.
Format:
[
  {
    "ingredient": "name",
    "status": "halal|haram|questionable",
    "reason": "one sentence max 10 words"
  }
]"""


def classify_unknown_ingredients(ingredients: list[str], madhab: str) -> list[dict]:
    if not ingredients:
        return []

    client = Groq(api_key=settings.GROQ_API_KEY)

    madhab_context = MADHAB_RULES.get(madhab, MADHAB_RULES['hanafi'])

    user_message = f"""Madhab: {madhab.upper()}

{madhab_context}

Classify these ingredients:
{json.dumps(ingredients, ensure_ascii=False)}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_BASE},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if part.startswith("json"):
                    raw = part[4:].strip()
                    break
                elif "[" in part:
                    raw = part.strip()
                    break
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            raw = raw[start:end]
        return json.loads(raw.strip())
    except Exception as e:
        return [
            {"ingredient": ing, "status": "questionable", "reason": f"Could not classify. Error: {str(e)}"}
            for ing in ingredients
        ]