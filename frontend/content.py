"""Static content + helpers for the UI (class info, colours, report loading)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "evaluation.json"

# Keyed by the class names the model returns. Unknown names fall back to DEFAULT.
CLASS_INFO: Dict[str, Dict[str, str]] = {
    "Paper": {
        "icon": "📄", "color": "#60a5fa",
        "tip": "Keep it dry and clean. Wet or greasy paper is usually not accepted for recycling.",
    },
    "Plastic Bottle": {
        "icon": "🍼", "color": "#34d399",
        "tip": "Empty and rinse it. Many collectors want the cap on and the bottle crushed.",
    },
    "Plastic bag": {
        "icon": "🛍️", "color": "#fbbf24",
        "tip": "Thin bags often jam sorting machines. Look for a dedicated drop-off point.",
    },
    "Plastic waste": {
        "icon": "🧴", "color": "#f87171",
        "tip": "Mixed plastics vary a lot. Check your local rules before placing it in recycling.",
    },
}
DEFAULT_INFO = {"icon": "♻️", "color": "#64748b", "tip": "Check your local recycling rules."}


def info(name: str) -> Dict[str, str]:
    return CLASS_INFO.get(name, DEFAULT_INFO)


def load_report() -> Optional[dict]:
    """Read reports/evaluation.json if present, so the page updates after retraining."""
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def per_class_rows(report: dict, split: str = "test") -> List[dict]:
    rows = []
    for c in (report.get(split) or {}).get("per_class", []):
        rows.append({
            "Class": c["class_name"],
            "Precision": round(c["precision"], 3),
            "Recall": round(c["recall"], 3),
            "mAP50": round(c["mAP50"], 3),
            "mAP50-95": round(c["mAP50-95"], 3),
        })
    return rows
