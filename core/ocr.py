import base64
import json
from groq import Groq
from django.conf import settings


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

    prompt = f"""You are a strict Islamic halal food auditor. Analyze this food product label image.

STEP 1 — HALAL LOGO CHECK:
Look carefully for any halal certification logo, stamp, or marking on the label.
Examples: MUI, JAKIM, IFANCA, HFA, ISWA, HMC, or any text saying "Halal Certified".
Set has_halal_logo to true ONLY if you clearly see one. Do not guess.

STEP 2 — EXTRACT INGREDIENTS:
Extract the full ingredient list exactly as written on the label.

STEP 3 — CLASSIFY EACH INGREDIENT:
Use these strict rules based on madhab: {madhab}

UNIVERSAL HARAM (both madhabs):
- Pork, lard, pig-derived anything → haram
- Blood and blood products → haram
- Alcohol as a main ingredient (wine, beer, spirits) → haram
- Any ingredient explicitly stated as pork-derived or animal-derived from non-halal slaughter → haram
- Carmine / E120 / cochineal (insect-derived red dye) → haram
- L-Cysteine (E920) from pork or human hair → haram

ANIMAL-DERIVED AMBIGUOUS INGREDIENTS — BE VERY CAREFUL:
- Gelatin: if source not specified → questionable. If stated as pork → haram. If stated as fish/halal beef → halal.
- Glycerin/Glycerol: if source not stated → questionable. If "vegetable glycerin" → halal.
- Mono and diglycerides (E471): source not stated → questionable.
- Saturated fat: if explicitly stated as animal fat → haram. If source unclear → questionable. If stated as vegetable → halal.
- Natural flavor / Natural flavouring: always → questionable (source unknown).
- Artificial flavor: → questionable (may contain animal derivatives).
- Rennet: if animal rennet not specified as halal → questionable.
- Whey: → questionable (depends on rennet used in cheese).
- Casein / Sodium caseinate: → questionable.
- Enzymes: if source not stated → questionable.
- Lecithin: if "soy lecithin" or "sunflower lecithin" → halal. If just "lecithin" → questionable.
- Vitamin D3: often animal-derived → questionable unless stated as plant-based.
- Omega-3: if from fish → halal (both madhabs). If source unclear → questionable.

MADHAB-SPECIFIC RULES:
{"HANAFI RULES: Only scaled fish (bony fish) are halal. Shrimp, prawns, crab, lobster, squid, octopus, shellfish, mussels, oysters, clams, scallops are ALL HARAM in Hanafi madhab. Shark is haram in Hanafi." if madhab == "hanafi" else "SHAFI'I RULES: All seafood is halal including shrimp, prawns, crab, lobster, shellfish, squid, octopus, fish of all types."}

ALWAYS HALAL (both madhabs):
- All fruits, vegetables, grains, legumes, nuts, seeds
- Water, salt, sugar, vinegar
- Plant-based oils (palm, sunflower, canola, olive, soy, corn)
- Eggs (always halal, no exceptions)
- Milk and dairy from halal animals (cow, goat, sheep) UNLESS rennet is questionable
- Honey
- All spices and herbs
- Synthetic/mineral additives (E-numbers that are mineral or synthetic — e.g. E330 citric acid, E500 sodium carbonate, E202 potassium sorbate)
- Soy sauce (fermentation alcohol is trace and transformed)
- Vinegar of any type except wine vinegar which is questionable

GOLDEN RULE: If you are not 100% certain something is halal, mark it questionable. Never upgrade questionable to halal due to assumption. A false halal verdict is worse than a false haram verdict.

Respond ONLY with this exact valid JSON format, no extra text:
{{
  "has_halal_logo": true or false,
  "halal_logo_name": "certification body name or null",
  "ingredients_text": "full raw ingredient text extracted from label",
  "results": [
    {{
      "ingredient": "exact ingredient name",
      "status": "halal|haram|questionable",
      "reason": "max 10 words explaining why"
    }}
  ]
}}

If no ingredient list is visible: {{"has_halal_logo": false, "halal_logo_name": null, "ingredients_text": "", "results": []}}"""

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

        # Strip markdown fences
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                if part.startswith("json"):
                    raw = part[4:].strip()
                    break
                elif "{" in part:
                    raw = part.strip()
                    break

        # Find JSON object boundaries
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