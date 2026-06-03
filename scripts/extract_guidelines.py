#!/usr/bin/env python3
"""
Extract structured rules from legislative guideline PDFs using an LLM.

Usage:
    python scripts/extract_guidelines.py [--source FILE] [--all]

Reads PDFs from backend/data/guidelines/sources/ and writes structured
JSON rule catalogs to backend/data/guidelines/extracted/.

Requires: DEEPINFRA_API_KEY env var or .env file.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / "backend" / "data" / "guidelines" / "sources"
OUTPUT_DIR = ROOT / "backend" / "data" / "guidelines" / "extracted"

MODEL = "Qwen/Qwen3.5-397B-A17B"
API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
MAX_CHARS_PER_CHUNK = 60_000  # ~15k tokens per chunk

EXTRACTION_PROMPT = """\
Du bist ein Experte für deutsche Gesetzgebungslehre. Analysiere den folgenden Textausschnitt \
aus dem Dokument "{doc_title}" und extrahiere ALLE konkreten, prüfbaren Regeln, Vorgaben, \
Muss-/Soll-Bestimmungen und Checklisten-Punkte.

Für jede Regel gib zurück:
- "id": eindeutige Kennung (Dokumentkürzel + fortlaufende Nummer, z.B. "hdr-001")
- "category": thematische Kategorie (z.B. "Überschriften", "Verweisungen", "Inkrafttreten")
- "rule": die Regel als prägnanter, vollständiger Satz
- "verbindlichkeit": "muss" | "soll" | "kann" | "empfehlung"
- "applies_to": Liste der Workflow-Schritte, in denen die Regel relevant ist. \
Mögliche Werte: ["norm_identification", "proposal_development", "evaluation", "amendment", "entwurf"]
- "source_section": Abschnitt/Randnummer im Originaldokument (falls erkennbar)

Antworte ausschliesslich mit einem JSON-Array. Keine Erklärungen, kein Markdown.
Wenn der Textausschnitt keine extrahierbaren Regeln enthält, antworte mit [].

Dokumentkürzel für IDs: "{doc_abbrev}"
Bisherige höchste ID-Nummer: {last_id_num}

--- TEXTAUSSCHNITT ---
{text_chunk}
"""

MERGE_PROMPT = """\
Du erhältst mehrere JSON-Arrays mit extrahierten Regeln aus demselben Dokument "{doc_title}". \
Führe sie zu einem einzigen, deduplizierten Array zusammen. Entferne exakte Duplikate und \
fasse sehr ähnliche Regeln zusammen. Nummeriere die IDs fortlaufend neu (Format: "{doc_abbrev}-001", \
"{doc_abbrev}-002", etc.).

Antworte ausschliesslich mit dem finalen JSON-Array.

--- REGEL-ARRAYS ---
{chunks_json}
"""


def get_api_key() -> str:
    key = os.environ.get("DEEPINFRA_API_KEY", "")
    if not key:
        print("ERROR: DEEPINFRA_API_KEY not set. Set it in .env or environment.")
        sys.exit(1)
    return key


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF (fitz) or pdfplumber."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except ImportError:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        pass

    print("ERROR: Install PyMuPDF or pdfplumber: pip install pymupdf pdfplumber")
    sys.exit(1)


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def call_llm(prompt: str, api_key: str) -> str:
    """Call DeepInfra LLM and return response text."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 16384,
    }

    timeout = httpx.Timeout(600.0)
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(API_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        print(f"  API error {resp.status_code}: {resp.text[:500]}")
        return "[]"

    result = resp.json()
    content = result["choices"][0]["message"]["content"]

    # Strip thinking blocks and markdown wrappers
    if "<think>" in content:
        think_end = content.rfind("</think>")
        if think_end != -1:
            content = content[think_end + len("</think>"):].strip()

    if "```json" in content:
        start = content.find("```json") + len("```json")
        end = content.find("```", start)
        if end != -1:
            content = content[start:end].strip()
    elif content.startswith("```"):
        start = content.find("\n")
        end = content.rfind("```")
        if start != -1 and end > start:
            content = content[start:end].strip()

    return content


def parse_json_safe(text: str) -> list:
    """Parse JSON array, returning empty list on failure."""
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        # Try to find JSON array in text
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        print(f"  WARNING: Could not parse JSON response")
        return []


def derive_doc_info(filename: str) -> tuple[str, str]:
    """Derive document abbreviation and title from filename."""
    stem = Path(filename).stem

    known = {
        "hdr": ("hdr", "Handbuch der Rechtsförmlichkeit"),
        "ggo": ("ggo", "Gemeinsame Geschäftsordnung der Bundesministerien"),
        "gfa": ("gfa", "Arbeitshilfe zur Gesetzesfolgenabschätzung"),
        "nkr": ("nkr", "Leitlinien des Nationalen Normenkontrollrats"),
        "digitalcheck": ("digck", "Digitalcheck / Digitaltauglichkeitsprüfung"),
        "nachhaltigkeitspruefung": ("nhp", "Nachhaltigkeitsprüfung"),
        "blaue_prueffragen": ("blau", "Blaue Prüffragen"),
    }

    stem_lower = stem.lower().replace("-", "_").replace(" ", "_")
    for key, (abbrev, title) in known.items():
        if key in stem_lower:
            return abbrev, title

    # Fallback: use first 4 chars of filename
    abbrev = stem_lower[:4].replace("_", "")
    return abbrev, stem


def process_pdf(pdf_path: Path, api_key: str) -> dict:
    """Process a single PDF and return the guideline catalog."""
    doc_abbrev, doc_title = derive_doc_info(pdf_path.name)

    print(f"\nProcessing: {pdf_path.name}")
    print(f"  Title: {doc_title}")
    print(f"  Abbreviation: {doc_abbrev}")

    # Extract text
    print("  Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    print(f"  Extracted {len(text):,} characters")

    if len(text) < 100:
        print("  WARNING: Very little text extracted. PDF may be image-based.")
        print("  Consider using OCR first (e.g. ocrmypdf).")
        return {"id": doc_abbrev, "name": doc_title, "rules": []}

    # Chunk text
    chunks = chunk_text(text)
    print(f"  Split into {len(chunks)} chunks")

    # Extract rules from each chunk
    all_rules = []
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i + 1}/{len(chunks)}...")
        prompt = EXTRACTION_PROMPT.format(
            doc_title=doc_title,
            doc_abbrev=doc_abbrev,
            last_id_num=len(all_rules),
            text_chunk=chunk,
        )
        response = call_llm(prompt, api_key)
        rules = parse_json_safe(response)
        print(f"    Extracted {len(rules)} rules")
        all_rules.extend(rules)

        # Rate limiting
        if i < len(chunks) - 1:
            time.sleep(1)

    print(f"  Total raw rules: {len(all_rules)}")

    # Merge and deduplicate if we have multiple chunks
    if len(chunks) > 1 and all_rules:
        print("  Merging and deduplicating...")

        # Split into batches for merge (avoid exceeding context)
        batch_size = 200
        if len(all_rules) > batch_size:
            # Merge in batches
            merged = []
            for batch_start in range(0, len(all_rules), batch_size):
                batch = all_rules[batch_start:batch_start + batch_size]
                prompt = MERGE_PROMPT.format(
                    doc_title=doc_title,
                    doc_abbrev=doc_abbrev,
                    chunks_json=json.dumps(batch, ensure_ascii=False, indent=2),
                )
                response = call_llm(prompt, api_key)
                merged.extend(parse_json_safe(response))
                time.sleep(1)
            all_rules = merged
        else:
            prompt = MERGE_PROMPT.format(
                doc_title=doc_title,
                doc_abbrev=doc_abbrev,
                chunks_json=json.dumps(all_rules, ensure_ascii=False, indent=2),
            )
            response = call_llm(prompt, api_key)
            merged = parse_json_safe(response)
            if merged:
                all_rules = merged

    print(f"  Final rules: {len(all_rules)}")

    return {
        "id": doc_abbrev,
        "name": doc_title,
        "source_file": pdf_path.name,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rule_count": len(all_rules),
        "rules": all_rules,
    }


def main():
    parser = argparse.ArgumentParser(description="Extract rules from legislative guideline PDFs")
    parser.add_argument("--source", type=str, help="Process a specific PDF file (name or path)")
    parser.add_argument("--all", action="store_true", help="Process all PDFs in sources/")
    parser.add_argument("--model", type=str, default=MODEL, help=f"LLM model to use (default: {MODEL})")
    args = parser.parse_args()

    global MODEL
    if args.model:
        MODEL = args.model

    api_key = get_api_key()

    # Determine which PDFs to process
    if args.source:
        source_path = Path(args.source)
        if not source_path.is_absolute():
            source_path = SOURCES_DIR / source_path
        if not source_path.exists():
            print(f"ERROR: File not found: {source_path}")
            sys.exit(1)
        pdfs = [source_path]
    elif args.all:
        pdfs = sorted(SOURCES_DIR.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {SOURCES_DIR}")
            print("Place PDF files there and run again.")
            sys.exit(1)
    else:
        pdfs = sorted(SOURCES_DIR.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {SOURCES_DIR}")
            print(f"\nUsage:")
            print(f"  1. Place PDF files in: {SOURCES_DIR}")
            print(f"  2. Run: python scripts/extract_guidelines.py --all")
            print(f"  3. Or for a single file: python scripts/extract_guidelines.py --source filename.pdf")
            sys.exit(0)
        # Interactive: list available PDFs
        print(f"Found {len(pdfs)} PDF(s) in {SOURCES_DIR}:")
        for i, pdf in enumerate(pdfs):
            print(f"  [{i + 1}] {pdf.name}")
        print(f"\nRun with --all to process all, or --source <name> for one.")
        sys.exit(0)

    # Process each PDF
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for pdf in pdfs:
        catalog = process_pdf(pdf, api_key)

        output_file = OUTPUT_DIR / f"{catalog['id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        print(f"  Saved to: {output_file}")

    # Generate combined index
    all_catalogs = []
    for json_file in sorted(OUTPUT_DIR.glob("*.json")):
        if json_file.name == "index.json":
            continue
        with open(json_file, encoding="utf-8") as f:
            catalog = json.load(f)
        all_catalogs.append({
            "id": catalog["id"],
            "name": catalog["name"],
            "rule_count": catalog["rule_count"],
            "file": json_file.name,
        })

    index_file = OUTPUT_DIR / "index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(all_catalogs, f, ensure_ascii=False, indent=2)

    print(f"\nIndex updated: {index_file}")
    print(f"Total guidelines: {len(all_catalogs)}")
    print(f"Total rules: {sum(c['rule_count'] for c in all_catalogs)}")


if __name__ == "__main__":
    main()
