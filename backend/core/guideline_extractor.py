"""Extract guideline rules from uploaded PDF documents using an LLM."""

import json
import re
from typing import Optional

import fitz  # pymupdf

from .llm_service import query_llm


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 50) -> str:
    """Extract text content from a PDF file."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pages.append(page.get_text())
    doc.close()
    return "\n\n".join(pages)


_EXTRACTION_PROMPT = """\
Du bist ein Experte für deutsche Gesetzgebungsmethodik und Legistik.

Analysiere den folgenden Text eines Leitfadens und extrahiere alle konkreten Regeln, \
Vorgaben und Prüfpunkte, die bei der Erstellung von Gesetzesänderungen beachtet werden müssen.

Für jede Regel bestimme:
1. **category**: Eine kurze Kategorie-Bezeichnung (z.B. "Sprachliche Gestaltung", "Verweisungen", "Übergangsrecht")
2. **rule**: Den vollständigen Regeltext als einen Satz
3. **verbindlichkeit**: "muss" (zwingend), "soll" (grundsätzlich verbindlich) oder "kann" (optional/empfohlen)
4. **applies_to**: Liste der Workflow-Schritte, für die die Regel relevant ist. \
Mögliche Werte: \
"norm_identification" (Regelungskontext: Identifikation relevanter Normen), \
"proposal_development" (Regelungsalternativen: Entwicklung von Änderungsvorschlägen), \
"evaluation" (Evaluierung: Bewertung der Vorschläge), \
"amendment" (Umsetzung: Erstellung des Änderungswortlauts), \
"entwurf" (Gesetzesentwurf: Erstellung des finalen Entwurfs). \
Wenn eine Regel für alle Schritte gilt, verwende ein leeres Array [].
5. **source_section**: Die Abschnitts-/Kapitelbezeichnung aus dem Originaldokument

Antworte ausschließlich mit einem JSON-Objekt im folgenden Format:
{{
  "name": "<Vollständiger Name des Leitfadens>",
  "source": "<Herausgebende Institution>",
  "rules": [
    {{
      "category": "...",
      "rule": "...",
      "verbindlichkeit": "muss|soll|kann",
      "applies_to": [...],
      "source_section": "..."
    }}
  ]
}}

Hier ist der Text des Leitfadens:

{text}
"""


async def extract_rules_from_pdf(
    pdf_bytes: bytes,
    api_key: str,
    model: str,
    catalog_id: str,
    custom_name: Optional[str] = None,
) -> dict:
    """Parse a PDF and use an LLM to extract structured guideline rules.

    Args:
        pdf_bytes: Raw PDF file content.
        api_key: LLM API key.
        model: LLM model identifier.
        catalog_id: Unique ID for the new catalog (e.g. slug of the filename).
        custom_name: Optional display name override.

    Returns:
        A complete catalog dict ready to be saved as JSON.
    """
    text = extract_text_from_pdf(pdf_bytes)
    if not text.strip():
        raise ValueError("Das PDF enthält keinen extrahierbaren Text.")

    # Truncate very long documents to avoid token limits
    if len(text) > 60_000:
        text = text[:60_000] + "\n\n[... Text wurde gekürzt ...]"

    prompt = _EXTRACTION_PROMPT.format(text=text)
    raw_response = await query_llm(prompt, api_key, model)

    # Parse the JSON from the LLM response
    try:
        extracted = json.loads(raw_response)
    except json.JSONDecodeError:
        # Try to find JSON block in the response
        match = re.search(r"\{[\s\S]*\}", raw_response)
        if match:
            extracted = json.loads(match.group())
        else:
            raise ValueError("Das LLM hat kein gültiges JSON zurückgegeben.")

    rules = extracted.get("rules", [])

    # Assign unique IDs to each rule
    for i, rule in enumerate(rules, start=1):
        rule["id"] = f"{catalog_id}-{i:02d}"

    catalog = {
        "id": catalog_id,
        "name": custom_name or extracted.get("name", catalog_id),
        "source": extracted.get("source", "Benutzerdefiniert"),
        "version": "Benutzerdefiniert",
        "url": "",
        "rule_count": len(rules),
        "rules": rules,
    }

    return catalog
