#!/usr/bin/env python3
"""Quick test of Gemini API connectivity and response parsing."""
import asyncio
import sys
from pathlib import Path
from analyzer import analyze, GeoResult

# Create a simple test image (just a white PNG)
def create_test_image() -> bytes:
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (800, 600), color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


async def main():
    print("Testing Gemini API connectivity...")

    if not Path(".env").exists():
        print("✗ .env file not found. Create it with: cp .env.example .env")
        print("  Then add your GEMINI_API_KEY")
        sys.exit(1)

    try:
        image_bytes = create_test_image()
        print("  Generated test image...")

        result = await analyze(image_bytes)
        print(f"✓ API response received:")
        print(f"  Country: {result.country}")
        print(f"  Coordinates: {result.lat}, {result.lon}")
        print(f"  Confidence: {result.confidence}%")
        print(f"  Explanation: {result.explanation}")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
