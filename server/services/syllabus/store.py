"""Syllabus storage and LLM-based parsing."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_STORE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "syllabuses"


def _ensure_dir() -> Path:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORE_DIR


def list_syllabuses() -> List[Dict[str, Any]]:
    d = _ensure_dir()
    results = []
    for meta_file in sorted(d.glob("*.json")):
        try:
            results.append(json.loads(meta_file.read_text()))
        except Exception:
            pass
    return results


def get_syllabus(course_id: str) -> Optional[Dict[str, Any]]:
    meta_file = _ensure_dir() / f"{course_id}.json"
    if not meta_file.exists():
        return None
    try:
        return json.loads(meta_file.read_text())
    except Exception:
        return None


def get_syllabus_raw(course_id: str) -> Optional[str]:
    raw_file = _ensure_dir() / f"{course_id}.raw"
    return raw_file.read_text(encoding="utf-8") if raw_file.exists() else None


def delete_syllabus(course_id: str) -> bool:
    d = _ensure_dir()
    deleted = False
    for ext in (".json", ".raw"):
        f = d / f"{course_id}{ext}"
        if f.exists():
            f.unlink()
            deleted = True
    return deleted


def save_syllabus(
    course_id: str,
    course_name: str,
    raw_text: str,
    topics: List[str],
    exam_hints: List[str],
) -> Dict[str, Any]:
    d = _ensure_dir()
    meta: Dict[str, Any] = {
        "course_id": course_id,
        "course_name": course_name,
        "topics": topics,
        "exam_hints": exam_hints,
        "topic_count": len(topics),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        (d / f"{course_id}.json").write_text(json.dumps(meta, indent=2))
        (d / f"{course_id}.raw").write_text(raw_text, encoding="utf-8")
    return meta


async def parse_syllabus_with_llm(raw_text: str, filename: str) -> Dict[str, Any]:
    """Use Haiku to extract course name, topics, and exam hints from raw text."""
    import os
    import httpx

    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("EXECUTION_MODEL", "claude-haiku-4-5-20251001")

    user_msg = (
        f"Parse this syllabus (filename: {filename}) and return ONLY a JSON object with:\n"
        '- "course_name": full course name/title (string)\n'
        '- "topics": ordered list of topic/chapter/unit names to study (list of strings, 5-30 items)\n'
        '- "exam_hints": any exam, midterm, or final dates or descriptions mentioned (list of strings)\n\n'
        "Return ONLY valid JSON. No explanation, no markdown fences.\n\n"
        f"Syllabus text:\n{raw_text[:8000]}"
    )

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": user_msg}],
            },
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        # Strip markdown fences if the model added them
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1].lstrip("json").strip() if len(parts) > 1 else text
        return json.loads(text)


__all__ = [
    "delete_syllabus",
    "get_syllabus",
    "get_syllabus_raw",
    "list_syllabuses",
    "parse_syllabus_with_llm",
    "save_syllabus",
]
