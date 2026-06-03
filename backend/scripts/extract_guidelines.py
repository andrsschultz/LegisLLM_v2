"""Batch-extract guideline rules from all PDFs in backend/data/guidelines/sources/.

Usage:
    python -m backend.scripts.extract_guidelines --api-key <KEY> [--model <MODEL>]

Reads every .pdf in sources/, runs the LLM extraction, and saves the result
as JSON in extracted/.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Resolve paths relative to this file
SOURCES_DIR = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "sources"
EXTRACTED_DIR = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "extracted"


async def process_pdf(pdf_path: Path, api_key: str, model: str) -> None:
    # Import here so the module path works with -m
    from backend.core.guideline_extractor import extract_rules_from_pdf

    catalog_id = pdf_path.stem  # e.g. "hdr", "ggo", "digitalcheck_bund"
    out_path = EXTRACTED_DIR / f"{catalog_id}.json"

    if out_path.exists():
        print(f"  Überspringe {pdf_path.name} (bereits vorhanden: {out_path.name})")
        return

    print(f"  Extrahiere Regeln aus {pdf_path.name} ...")
    pdf_bytes = pdf_path.read_bytes()

    catalog = await extract_rules_from_pdf(
        pdf_bytes=pdf_bytes,
        api_key=api_key,
        model=model,
        catalog_id=catalog_id,
    )

    import json
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out_path.name} ({catalog['rule_count']} Regeln)")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Extract guideline rules from source PDFs via LLM")
    parser.add_argument("--api-key", default=os.environ.get("DEEPINFRA_API_KEY", ""),
                        help="DeepInfra API key (or set DEEPINFRA_API_KEY env var)")
    parser.add_argument("--model", default="anthropic/claude-sonnet-4-6",
                        help="LLM model to use (default: anthropic/claude-sonnet-4-6)")
    parser.add_argument("--force", action="store_true",
                        help="Re-extract even if JSON already exists")
    args = parser.parse_args()

    if not args.api_key:
        print("Fehler: Kein API-Key angegeben. Nutze --api-key oder setze DEEPINFRA_API_KEY.")
        sys.exit(1)

    pdfs = sorted(SOURCES_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"Keine PDFs gefunden in {SOURCES_DIR}")
        sys.exit(1)

    print(f"Gefunden: {len(pdfs)} PDF(s) in {SOURCES_DIR}")
    print(f"Modell: {args.model}\n")

    for pdf_path in pdfs:
        if args.force:
            out_path = EXTRACTED_DIR / f"{pdf_path.stem}.json"
            if out_path.exists():
                out_path.unlink()
        await process_pdf(pdf_path, args.api_key, args.model)

    print("\nFertig.")


if __name__ == "__main__":
    asyncio.run(main())
