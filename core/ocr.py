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

    prompt = f"""Look at this food product label image.

1. Extract the ingredients list from the label.
2. Classify each ingredient as halal, haram, or questionable according to Islamic dietary law.
3. Madhab context: {madhab}

Keep reasons short (max 10 words each). Respond ONLY with valid JSON:
{{
  "ingredients_text": "raw ingredient text from image",
  "results": [
    {{
      "ingredient": "name",
      "status": "halal|haram|questionable",
      "reason": "short reason"
    }}
  ]
}}

If no ingredient list found, return: {{"ingredients_text": "", "results": []}}
"""

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

        return json.loads(raw)

    except Exception as e:
        raise ValueError(f"Image analysis failed: {str(e)}")