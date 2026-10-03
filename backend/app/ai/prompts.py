"""Prompt builders for the AI provider layer."""


def build_recognition_prompt() -> str:
    return """
You are a fashion and wardrobe recognition assistant.
Return ONLY valid JSON with the keys below and nothing else.

Requirements:
- Infer only what is visually supported.
- Use null for uncertain values.
- Keep category values from this exact set: Tops, Bottoms, Dresses, Outerwear, Shoes, Accessories, Bags.
- Keep patterns from this exact set: Solid, Striped, Checked, Floral, Polka dot, Graphic, Textured, Animal print, Other.
- Keep styles as a list of style terms like Casual, Smart casual, Minimal, Formal, Streetwear, Elegant, Vintage, Sporty, Bohemian.
- Return each numeric confidence score as a number between 0 and 1.
- Include a concise description and tags.

JSON schema:
{
  "item_name": "string",
  "category": "Tops",
  "subcategory": "string or null",
  "primary_colour": "string or null",
  "secondary_colour": "string or null",
  "pattern": "Solid",
  "material": "string or null",
  "texture": "string or null",
  "sleeve_type": "string or null",
  "neckline": "string or null",
  "fit": "string or null",
  "length": "string or null",
  "style": ["Casual"],
  "occasions": ["Everyday"],
  "seasons": ["Summer"],
  "formality": "Casual",
  "description": "string",
  "tags": ["string"],
  "confidence": {
    "category": 0.95,
    "primary_colour": 0.9,
    "pattern": 0.8,
    "material": 0.6
  }
}
""".strip()


def build_outfit_prompt(candidate_outfits: list[dict], request: dict) -> str:
    return f"""
You are a personal stylist. Using only the wardrobe items supplied below, propose up to 3 outfit recommendations.
Return valid JSON only.

Preferences:
{request}

Candidate outfits (already filtered for compatibility):
{candidate_outfits}

Rules:
- Pick only item IDs from the supplied wardrobe item IDs.
- If there are not enough compatible pieces, return an empty recommendations list.
- Do not invent clothing items.
- Return an array called 'recommendations'.
- Each recommendation must include title, description, occasion, style, item_ids, styling_tips, reasoning, compatibility_score.
- compatibility_score should be a number between 0 and 100.
- Ensure the recommendations are distinct.
""".strip()
