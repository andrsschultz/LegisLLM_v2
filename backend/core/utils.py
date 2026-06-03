import re
import os
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Laws index (built lazily from the gesetze-im-internet submodule)
# ---------------------------------------------------------------------------

# Resolved once per process: jurabk (canonical case) → absolute XML path
_laws_index: Optional[Dict[str, str]] = None

# Root of the gesetze-im-internet submodule (data branch)
_LAWS_SUBMODULE_DIR = Path(__file__).parent.parent / "laws" / "data" / "items"
# Legacy curated files kept as a fallback
_LAWS_LEGACY_DIR = Path(__file__).parent.parent / "data"

_JURABK_RE = re.compile(rb"<jurabk>([^<]+)</jurabk>")


def _extract_jurabk_bytes(xml_path: Path) -> Optional[str]:
    """Read the first 1 KB of an XML file and extract <jurabk>."""
    try:
        with xml_path.open("rb") as fh:
            chunk = fh.read(1024)
        m = _JURABK_RE.search(chunk)
        if m:
            return m.group(1).decode("utf-8", errors="replace").strip()
    except OSError:
        pass
    return None


def _build_laws_index() -> Dict[str, str]:
    index: Dict[str, str] = {}

    # 1. Primary source: gesetze-im-internet submodule
    if _LAWS_SUBMODULE_DIR.is_dir():
        for law_dir in _LAWS_SUBMODULE_DIR.iterdir():
            if not law_dir.is_dir():
                continue
            for xml_file in law_dir.glob("*.xml"):
                jurabk = _extract_jurabk_bytes(xml_file)
                if jurabk:
                    index[jurabk] = str(xml_file)

    # 2. Fallback: legacy backend/data/ files (may override with local versions)
    if _LAWS_LEGACY_DIR.is_dir():
        for xml_file in _LAWS_LEGACY_DIR.glob("*.xml"):
            jurabk = _extract_jurabk_bytes(xml_file)
            if jurabk and jurabk not in index:
                index[jurabk] = str(xml_file)

    return index


def _get_laws_index() -> Dict[str, str]:
    global _laws_index
    if _laws_index is None:
        _laws_index = _build_laws_index()
    return _laws_index


def get_available_laws() -> List[str]:
    """Return sorted list of all known jurabk abbreviations."""
    return sorted(_get_laws_index().keys())


def format_norm_reference(jurabk: str, enbez: str | None, paragraph: str | None = None) -> str:
    parts = [jurabk]
    if enbez:
        parts.append(enbez)
    if paragraph:
        parts.append(f"Abs. {paragraph}")
    return " ".join(parts)


_ROMAN_TO_ARABIC = {
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
    "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10",
    "XI": "11", "XII": "12", "XIII": "13", "XIV": "14",
}

def _normalize_jurabk(jurabk: str) -> list[str]:
    """Return candidate jurabk variants (e.g. roman → arabic for SGB books)."""
    candidates = [jurabk]
    parts = jurabk.split()
    if len(parts) >= 2 and parts[-1].upper() in _ROMAN_TO_ARABIC:
        arabic = _ROMAN_TO_ARABIC[parts[-1].upper()]
        candidates.append(" ".join(parts[:-1] + [arabic]))
    return candidates


def resolve_law_xml_path(data_dir: str, jurabk: str) -> str:
    """Return the XML file path for a given jurabk, using the laws index."""
    index = _get_laws_index()

    for candidate in _normalize_jurabk(jurabk):
        # Exact match first
        if candidate in index:
            return index[candidate]

        # Case-insensitive exact match
        candidate_lower = candidate.lower()
        for key, path in index.items():
            if key.lower() == candidate_lower:
                return path

        # Prefix match: "UStG" matches "UStG 1980" (model may omit the year)
        prefix = candidate_lower + " "
        for key, path in index.items():
            if key.lower().startswith(prefix):
                return path

    # Last resort: construct path in the supplied data_dir (preserves old behaviour)
    return str(Path(data_dir) / f"{jurabk}.xml")


def clean_json_string(json_string):
    """
    Clean JSON string by removing markdown code blocks if present.
    
    Args:
        json_string (str): The raw JSON string that may be wrapped in ```json ... ``` or ``` ... ```
        
    Returns:
        str: The cleaned JSON string without markdown code blocks
    """
    # Handle both ```json and plain ``` code blocks
    patterns = [
        r'^```json\s*(.*?)\s*```$',  # ```json ... ```
        r'^```\s*(.*?)\s*```$',     # ``` ... ```
    ]
    
    cleaned_string = json_string.strip()
    
    for pattern in patterns:
        match = re.search(pattern, cleaned_string, flags=re.DOTALL)
        if match:
            cleaned_string = match.group(1).strip()
            break
    
    return cleaned_string
