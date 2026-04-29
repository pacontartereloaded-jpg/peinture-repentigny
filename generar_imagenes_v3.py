# -*- coding: utf-8 -*-
"""
Generador de imagenes — Peinture Repentigny

Genera assets publicitarios para el sitio:
  1. Imagen base desde texto
  2. Imagen derivada usando la anterior como referencia visual

Uso recomendado en PowerShell:
  $env:GEMINI_API_KEY="tu_api_key"
  python generar_imagenes_v3.py

La API key no debe guardarse en este archivo ni en el repositorio.
"""

import argparse
import io
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: instala dependencias con: pip install -r requirements.txt")
    sys.exit(1)

try:
    from PIL import Image, ImageOps
except ImportError:
    print("ERROR: instala dependencias con: pip install -r requirements.txt")
    sys.exit(1)


MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")
OUTPUT_DIR = Path(__file__).parent / "public" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


ASSETS = [
    {
        "tipo": "logo",
        "nombre": "logo-peinture-repentigny-ai.png",
        "size": (1200, 1200),
        "prompt": (
            "Premium brand logo concept for a Quebec painting company named Peinture Repentigny. "
            "Clean professional emblem, lime green #8FB83A, deep charcoal #1A1A1A, warm white background. "
            "Include subtle paint roller or brush mark integrated with a house silhouette. "
            "Elegant, trustworthy, local contractor brand, minimal vector-like style, centered composition. "
            "No mockup, no business card, no wall sign, no extra text except Peinture Repentigny if readable."
        ),
    },
    {
        "tipo": "hero",
        "nombre": "hero-peinture-interieure-repentigny.jpg",
        "size": (1400, 1050),
        "prompt": (
            "Single continuous photorealistic real estate photo, not a collage, not split-screen, no before-after panel. "
            "Bright renovated living room in a Repentigny, Quebec family home, photographed with a natural 24mm wide-angle lens. "
            "Fresh warm light grey painted walls, crisp white trim, clean ceiling, elegant sofa, coffee table, hardwood floor, large window with soft daylight. "
            "The room must look finished and premium, not under construction. Add only one subtle sign of a painting contractor: "
            "a closed paint can and one clean brush placed neatly on a small protective cloth near the wall. "
            "No people, no text, no distorted architecture, no extra wall pasted on the side, no duplicate rooms, no vertical seam, realistic magazine-quality interior photography."
        ),
        "derivados": [
            {
                "nombre": "og-image.jpg",
                "size": (1200, 630),
                "prompt": (
                    "Use the same room and camera angle as reference. Create a website social sharing image for Peinture Repentigny. "
                    "Keep the renovated living room visible and premium, slightly wider composition, clean space on the left for future text, "
                    "professional painting contractor mood, no readable text, no people."
                ),
            }
        ],
    },
    {
        "tipo": "reference",
        "nombre": "artisan-peintre-preparation.jpg",
        "size": (1200, 1320),
        "prompt": (
            "Photorealistic close-up vertical image of a professional residential painting preparation scene. "
            "Protected hardwood floor, masking tape applied perfectly along white trim, premium paint tools arranged neatly, "
            "fresh lime-green accent color sample on the wall, clean high-end workmanship, Quebec home interior, no people, no text."
        ),
    },
]


PARES = [
    {
        "escena": "salon",
        "antes": "realisation-salon-avant.jpg",
        "despues": "realisation-salon-apres.jpg",
        "size": (900, 506),
        "prompt_antes": (
            "Photorealistic real estate photo of a Repentigny living room before painting. "
            "Old yellowed beige walls with scuff marks near the sofa and door frame. Grey fabric sofa on the left, "
            "wooden coffee table in center, floor lamp in right corner, dark curtains closed, bookshelf on right. "
            "Dull flat lighting, same wide angle camera, realistic dated interior, no people, no text."
        ),
        "prompt_despues": (
            "This is the exact same living room after a professional painting job. "
            "Keep the same room, same camera angle, same window, same sofa, same coffee table, same bookshelf and same lamp. "
            "Walls freshly painted in soft sage green with crisp white trim and ceiling. Curtains open with natural light. "
            "Only small lived-in changes: pillows spread apart, a throw blanket on the sofa, coffee mug and open magazine on table. "
            "Do not add or remove windows, doors, or large furniture. Real estate photography, no people, no text."
        ),
    },
    {
        "escena": "exterieur",
        "antes": "realisation-exterieur-avant.jpg",
        "despues": "realisation-exterieur-apres.jpg",
        "size": (900, 506),
        "prompt_antes": (
            "Photorealistic exterior real estate photo of a 1990s single-storey house in Le Gardeur, Quebec before painting. "
            "Faded beige siding, worn dark trim, slightly tired front door, small garden, driveway, cloudy natural light. "
            "Same camera angle from the street, realistic residential contractor portfolio image, no people, no text."
        ),
        "prompt_despues": (
            "This is the exact same house exterior after a professional painting job. "
            "Same camera angle, same windows, same driveway, same garden, same roofline. "
            "Siding freshly painted warm off-white, trim crisp charcoal, front door deep green matching #8FB83A brand tone, "
            "clean caulking lines and refreshed curb appeal. Only minor changes: brighter daylight and two potted plants near the entry. "
            "Do not change architecture or add windows. Photorealistic exterior real estate style, no people, no text."
        ),
    },
    {
        "escena": "armoires-cuisine",
        "antes": "realisation-armoires-avant.jpg",
        "despues": "realisation-armoires-apres.jpg",
        "size": (900, 506),
        "prompt_antes": (
            "Photorealistic real estate photo of a kitchen in Charlemagne, Quebec before cabinet refinishing. "
            "Old yellowed oak cabinets, dated brass handles, worn edges, beige walls, countertop with toaster and coffee maker, "
            "same camera angle, no people, no text, realistic dated kitchen."
        ),
        "prompt_despues": (
            "This is the exact same kitchen after professional cabinet refinishing and painting. "
            "Same camera angle, same countertop, same window, same appliances, same cabinet layout. "
            "Cabinets now smooth matte pure white, modern subtle hardware, walls freshly painted warm light grey, clean showroom finish. "
            "Only small lived-in changes: a fruit bowl appears near the toaster and a dish towel hangs from the oven handle. "
            "Do not change cabinet layout, windows, counters, or appliances. Photorealistic real estate style, no people, no text."
        ),
    },
]


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: define GEMINI_API_KEY como variable de entorno antes de ejecutar.")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def extraer_imagen(response):
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return None
    parts = getattr(candidates[0].content, "parts", None) or []
    for part in parts:
        if getattr(part, "inline_data", None) is not None:
            return Image.open(io.BytesIO(part.inline_data.data))
    return None


def guardar_web(img, path: Path, size):
    img = ImageOps.exif_transpose(img)
    if size:
        img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)

    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        img = img.convert("RGB")
        img.save(path, "JPEG", quality=88, optimize=True)
    else:
        img.save(path, "PNG", optimize=True)


def generar_texto(client, nombre, prompt, size=None, skip_existing=False):
    path = OUTPUT_DIR / nombre
    if skip_existing and path.exists():
        print(f"  SKIP -> {path}")
        return Image.open(path)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    img = extraer_imagen(response)
    if img is None:
        raise RuntimeError("Gemini no devolvio imagen")
    guardar_web(img, path, size)
    print(f"  OK -> {path}")
    return Image.open(path)


def generar_referencia(client, nombre, imagen_ref, prompt, size=None, skip_existing=False):
    path = OUTPUT_DIR / nombre
    if skip_existing and path.exists():
        print(f"  SKIP -> {path}")
        return Image.open(path)

    response = client.models.generate_content(
        model=MODEL,
        contents=[imagen_ref, prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    img = extraer_imagen(response)
    if img is None:
        raise RuntimeError("Gemini no devolvio imagen")
    guardar_web(img, path, size)
    print(f"  OK -> {path}")
    return Image.open(path)


def main():
    parser = argparse.ArgumentParser(description="Genera imagenes para Peinture Repentigny con Gemini.")
    parser.add_argument("--skip-existing", action="store_true", help="No regenera archivos ya existentes.")
    args = parser.parse_args()

    client = get_client()
    total = len(ASSETS) + sum(len(asset.get("derivados", [])) for asset in ASSETS) + len(PARES) * 2

    print("=" * 68)
    print("  Peinture Repentigny - Generador de assets con referencias")
    print("=" * 68)
    print(f"  Modelo  : {MODEL}")
    print(f"  Salida  : {OUTPUT_DIR}")
    print(f"  Total   : {total} imagenes")
    print("=" * 68)

    contador = 0
    exitosas = 0

    for asset in ASSETS:
        contador += 1
        print(f"\n[{contador}/{total}] {asset['tipo'].upper()} -> {asset['nombre']}")
        try:
            base = generar_texto(client, asset["nombre"], asset["prompt"], asset.get("size"), args.skip_existing)
            exitosas += 1
            for derivado in asset.get("derivados", []):
                contador += 1
                print(f"\n[{contador}/{total}] DERIVADO CON REFERENCIA -> {derivado['nombre']}")
                generar_referencia(client, derivado["nombre"], base, derivado["prompt"], derivado.get("size"), args.skip_existing)
                exitosas += 1
        except Exception as exc:
            print(f"  ERROR: {exc}")

    for par in PARES:
        print(f"\n======= {par['escena'].upper()} =======")
        try:
            contador += 1
            print(f"\n[{contador}/{total}] ANTES -> {par['antes']}")
            antes = generar_texto(client, par["antes"], par["prompt_antes"], par.get("size"), args.skip_existing)
            exitosas += 1

            contador += 1
            print(f"\n[{contador}/{total}] DESPUES CON REFERENCIA -> {par['despues']}")
            generar_referencia(client, par["despues"], antes, par["prompt_despues"], par.get("size"), args.skip_existing)
            exitosas += 1
        except Exception as exc:
            print(f"  ERROR: {exc}")

    print("\n" + "=" * 68)
    print(f"  Completado: {exitosas}/{total} imagenes generadas")
    print(f"  Carpeta   : {OUTPUT_DIR}")
    print("=" * 68)


if __name__ == "__main__":
    main()
