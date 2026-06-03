"""Load and serve extracted guideline rule catalogs."""

import json
import os
from pathlib import Path
from typing import Optional

GUIDELINES_DIR = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "extracted"

_cache: dict[str, dict] = {}


def _load_catalogs() -> dict[str, dict]:
    """Load all guideline catalogs from JSON files (cached)."""
    if _cache:
        return _cache

    if not GUIDELINES_DIR.exists():
        return {}

    for json_file in sorted(GUIDELINES_DIR.glob("*.json")):
        if json_file.name == "index.json":
            continue
        with open(json_file, encoding="utf-8") as f:
            catalog = json.load(f)
        _cache[catalog["id"]] = catalog

    return _cache


def get_available_guidelines(include_rules: bool = False) -> list[dict]:
    """Return list of available guidelines (id, name, rule_count, optionally rules)."""
    catalogs = _load_catalogs()
    result = []
    for c in catalogs.values():
        entry: dict = {
            "id": c["id"],
            "name": c["name"],
            "rule_count": c.get("rule_count", len(c.get("rules", []))),
            "source": c.get("source", ""),
        }
        if include_rules:
            entry["rules"] = c.get("rules", [])
        result.append(entry)
    return result


def get_rules_for_step(
    guideline_ids: list[str],
    step: str,
    excluded_rule_ids: list[str] | None = None,
) -> list[dict]:
    """Get all rules from selected guidelines that apply to a given workflow step.

    Args:
        guideline_ids: List of guideline IDs to include (e.g. ["hdr", "gfa"])
        step: Workflow step name ("norm_identification", "proposal_development",
              "evaluation", "amendment", "entwurf")
        excluded_rule_ids: Optional list of individual rule IDs to exclude.

    Returns:
        List of rule dicts filtered to the given step.
    """
    catalogs = _load_catalogs()
    excluded = set(excluded_rule_ids or [])
    rules = []

    for gid in guideline_ids:
        catalog = catalogs.get(gid)
        if not catalog:
            continue
        for rule in catalog.get("rules", []):
            if rule.get("id") in excluded:
                continue
            applies = rule.get("applies_to", [])
            if step in applies or not applies:
                rules.append(rule)

    return rules


def format_rules_for_prompt(
    guideline_ids: list[str],
    step: str,
    excluded_rule_ids: list[str] | None = None,
    custom_rules: list[str] | None = None,
) -> str:
    """Format relevant rules as a text block for LLM prompt injection.

    custom_rules: Pre-formatted rule strings from client-side custom
        guidelines (stored in the user's browser, not on the server).

    Returns an empty string if no rules apply.
    """
    rules = get_rules_for_step(guideline_ids, step, excluded_rule_ids)
    extra = custom_rules or []
    if not rules and not extra:
        return ""

    lines = ["Beachte bei deiner Antwort die folgenden Vorgaben aus den ausgewählten Leitfäden:\n"]
    for rule in rules:
        verbindlichkeit = rule.get("verbindlichkeit", "").upper()
        prefix = f"[{verbindlichkeit}]" if verbindlichkeit else ""
        lines.append(f"- {prefix} {rule['rule']}")
    for r in extra:
        lines.append(f"- {r}")

    return "\n".join(lines)


def reload_catalogs():
    """Force reload of all catalogs (e.g. after extraction)."""
    _cache.clear()
    _load_catalogs()
