import base64
import json
from groq import Groq
from django.conf import settings

MADHAB_RULES = {
    'hanafi': """HANAFI RULES (strictest on seafood):
- Only scaled bony fish are halal
- Shrimp, prawns, crab, lobster, squid, octopus, shellfish, mussels, oysters, clams, scallops = HARAM
- Shark = HARAM
- Horse = HARAM
- Wine vinegar = HARAM""",

    'maliki': """MALIKI RULES:
- All fish halal
- Shrimp, prawns = HALAL
- Crab, lobster, shellfish = HARAM
- Shark = HALAL
- Horse = HALAL
- Wine vinegar = HALAL""",

    'shafii': """SHAFI'I RULES (most permissive on seafood):
- All seafood halal without exception
- Shrimp, prawns, crab, lobster, shellfish, squid, octopus = HALAL
- Shark = HALAL
- Horse = HALAL
- Wine vinegar = HALAL""",

    'hanbali': """HANBALI RULES:
- All fish halal
- Shrimp, prawns = HALAL
- Crab, lobster = HALAL
- Shark = HALAL
- Horse = HALAL
- Wine vinegar = HARAM""",
}


def extract_and_classify_from_image(image_file, madhab: str) -> dict:
    client = Groq(api_key=settings.GROQ_API_KEY)

    image_data = image_file.read()
    base64_image = base64.b64encode(image_data).decode('utf-8')

    filename = getattr(image_file, 'name', 'image.jpg').lower()
    if filename.endswith('.png'):
        media_type = 'image/png'
    elif filename.endswith('.webp'):
        media_type = 'image/webp'
    else:
        media_type = 'image/jpeg'

    madhab_context = MADHAB_RULES.get(madhab, MADHAB_RULES['hanafi'])

    prompt = f"""You are a strict Islamic halal food auditor with knowledge of all four schools of thought. Analyze this food product label image.

STEP 1 — HALAL LOGO CHECK:
Look for any halal certification logo, stamp, or marking.
Examples: MUI, JAKIM, IFANCA, HFA, ISWA, HMC, or any text saying "Halal Certified".
Set has_halal_logo to true ONLY if you clearly see one.

STEP 2 — EXTRACT INGREDIENTS:
Extract the full ingredient list exactly as written on the label.

STEP 3 — CLASSIFY EACH INGREDIENT:
Madhab: {madhab.upper()}

{madhab_context}

UNIVERSAL HARAM (all madhabs):
- Pork, lard, pig-derived anything → haram
- Blood and blood products → haram
- Alcohol as main ingredient (wine, beer, spirits) → haram
- Carmine / E120 / cochineal → haram
- L-Cysteine (E920) from pork or human hair → haram

AMBIGUOUS — QUESTIONABLE IF SOURCE UNKNOWN:
- Gelatin: unspecified source → questionable. Pork → haram. Fish/halal beef → halal.
- Glycerin/Glycerol: vegetable → halal. Unspecified → questionable.
- Mono and diglycerides (E471): unspecified → questionable.
- Natural flavour/flavoring: always → questionable.
- Artificial flavoring: → questionable.
- Rennet: animal unspecified → questionable.
- Whey, casein, sodium caseinate: → questionable.
- Enzymes: unspecified source → questionable.
- Lecithin: soy/sunflower lecithin → halal. Just "lecithin" → questionable.
- Vitamin D3: → questionable unless stated plant-based.
- Saturated fat: animal-stated → haram. Vegetable-stated → halal. Unclear → questionable.

ALWAYS HALAL:
- All fruits, vegetables, grains, legumes, nuts, seeds
- Water, salt, sugar, honey, all spices and herbs
- Plant-based oils (palm, sunflower, canola, olive, soy, corn)
- Eggs (always halal, no exceptions in any madhab)
- Milk and dairy from halal animals UNLESS rennet is questionable
- Synthetic/mineral E-numbers (E330, E500, E202, E211 etc.)
- Soy sauce (trace fermentation alcohol is transformed)

GOLDEN RULE: If not 100% certain something is halal, mark it questionable.
A false halal verdict is worse than a false haram verdict.

Respond ONLY with this exact JSON format, no extra text:
{{
  "has_halal_logo": true or false,
  "halal_logo_name": "certification body name or null",
  "ingredients_text": "full raw ingredient text extracted from label",
  "results": [
    {{
      "ingredient": "exact ingredient name",
      "status": "halal|haram|questionable",
      "reason": "max 10 words"
    }}
  ]
}}

If no ingredient list visible: {{"has_halal_logo": false, "halal_logo_name": null, "ingredients_text": "", "results": []}}"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{base64_image}"}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=4000,
        )

        raw = response.choices[0].message.content.strip()

        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if part.startswith("json"):
                    raw = part[4:].strip()
                    break
                elif "{" in part:
                    raw = part.strip()
                    break

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            fix_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": f"Fix this broken JSON and return only valid JSON, nothing else:\n{raw}"}
                ],
                max_tokens=4000,
            )
            fixed = fix_response.choices[0].message.content.strip()
            start = fixed.find("{")
            end = fixed.rfind("}") + 1
            if start != -1 and end > start:
                fixed = fixed[start:end]
            return json.loads(fixed)

    except Exception as e:
        raise ValueError(f"Image analysis failed: {str(e)}")