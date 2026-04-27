import asyncio
import json
from dataclasses import dataclass
import google.generativeai as genai
from config import GEMINI_API_KEY, MODEL


@dataclass
class GeoResult:
    lat: float
    lon: float
    country: str
    confidence: int
    explanation: str
    tokens_in: int = 0
    tokens_out: int = 0


SYSTEM_PROMPT = """You are a world-class GeoGuessr player with expert knowledge of every country's visual signatures. Analyze the street-view screenshot and pinpoint the location as precisely as possible.

IGNORE completely: GeoGuessr UI, minimap, score, timer, compass, buttons, any game interface overlay.

Analyze everything visible in the real world:

SIGNS & TEXT
- Road signs: shape, color, font, language, script, content
- Street names, house numbers, shop names, billboards, ads
- License plates style and color
- Warning/speed signs design

INFRASTRUCTURE
- Road surface, markings, lane dividers, curb style
- Utility poles: wooden/concrete/metal, wire arrangement
- Bollards: shape, color, stripes
- Guardrails, barriers, fences
- Traffic lights design

ENVIRONMENT
- Vegetation: trees, plants, grass — biome clues
- Terrain: hills, flatlands, desert, coast
- Sky color, weather, sun angle (season/hemisphere hint)
- Soil and rock color

BUILDINGS & CULTURE
- Architecture style, roof shape, building materials
- Balcony style, window type
- Churches, mosques, temples — religion clue
- People's clothing if visible
- Cars and their plates

GOOGLE CAR ARTIFACTS
- Camera blur, car shadow, antenna visible — can hint country

Combine ALL clues. Prioritize text and signs when readable. Give best coordinate estimate even if uncertain.

Return ONLY valid JSON (no markdown, no extra text):
{"lat": 0.0, "lon": 0.0, "country": "Country Name", "confidence": 0, "explanation": "2-3 sentences on key clues"}

- lat/lon: best coordinate estimate (not just country center)
- confidence: 1-100
- explanation: which specific clues determined the answer
"""


async def analyze(image_bytes: bytes) -> GeoResult:
    """Send image to Gemini and get location analysis."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL)

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

        usage = getattr(response, "usage_metadata", None)
        tokens_in = getattr(usage, "prompt_token_count", 0) or 0
        tokens_out = getattr(usage, "candidates_token_count", 0) or 0

        return GeoResult(
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            country=str(data["country"]),
            confidence=int(data["confidence"]),
            explanation=str(data["explanation"]),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    except KeyError as e:
        raise ValueError(f"Missing required field in response: {e}")
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}")
