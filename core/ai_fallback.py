import json
import os
from groq import Groq
from django.conf import settings

SYSTEM_PROMPT = """You are an Islamic dietary expert. Given a list of food ingredients, classify each as:
- halal: clearly permissible in Islam
- haram: clearly forbidden in Islam
- questionable: uncertain, debated among scholars

Respond ONLY with a valid JSON array. No explanation outside the JSON.
Format:
[
  {
    "ingredient": "name",
    "status": "halal|haram|questionable",
    "reason": "one sentence reason"
  }
]"""


def classify_unknown_ingredients(ingredients: list[str], madhab: str) -> list[dict]:
    if not ingredients:
        return []

    client = Groq(api_key=settings.GROQ_API_KEY)

    user_message = f"Madhab context: {madhab}\n\nClassify these ingredients:\n{json.dumps(ingredients, ensure_ascii=False)}"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return [
            {"ingredient": ing, "status": "questionable", "reason": f"Could not classify. Error: {str(e)}"}
            for ing in ingredients
        ]