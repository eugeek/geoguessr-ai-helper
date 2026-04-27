import asyncio
import json
from dataclasses import dataclass
import google.generativeai as genai
from config import GEMINI_API_KEY


@dataclass
class GeoResult:
    lat: float
    lon: float
    country: str
    confidence: int
    explanation: str


SYSTEM_PROMPT = """You are an expert GeoGuessr analyst. Your task is to analyze a screenshot and determine the location.

CRITICAL RULES:
- IGNORE all GeoGuessr UI elements (minimap, score, timer, compass, buttons, interface)
- Analyze ONLY the street-view world visible in the image
- Focus on these clues:
  * Road signs: style, language, color, text
  * Bollards/posts: shape, color, markings
  * Lane markings: color, pattern, style
  * Google Street View car stickers/metadata
  * Vegetation: biome, flora type
  * Soil/terrain: road surface, landscape
  * Architecture: building style, materials
  * Text on signs, billboards, shop names

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{"lat": 0.0, "lon": 0.0, "country": "Country Name", "confidence": 0, "explanation": "Brief explanation"}

Where:
- lat/lon: best estimate coordinates
- country: country name (English)
- confidence: 1-100 (100 = certain, 1 = wild guess)
- explanation: 1-2 sentences explaining the clues that led to this answer
"""


async def analyze(image_bytes: bytes) -> GeoResult:
    """Send image to Gemini and get location analysis."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            [{"mime_type": "image/png", "data": image_bytes}, SYSTEM_PROMPT],
        )

        # Extract JSON from response
        text = response.text.strip()

        # Handle markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)

        return GeoResult(
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            country=str(data["country"]),
            confidence=int(data["confidence"]),
            explanation=str(data["explanation"]),
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    except KeyError as e:
        raise ValueError(f"Missing required field in response: {e}")
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}")
