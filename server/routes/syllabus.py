"""Syllabus upload and management routes."""

from __future__ import annotations

import io
import re

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/syllabus", tags=["syllabus"])


def _extract_text_from_pdf(data: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        return data.decode("utf-8", errors="replace")


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]


@router.post("/upload")
async def upload_syllabus(
    file: UploadFile = File(...),
    course_name: str = Form(default=""),
) -> JSONResponse:
    from ..services.syllabus import parse_syllabus_with_llm, save_syllabus

    data = await file.read()
    filename = file.filename or "syllabus"

    if filename.lower().endswith(".pdf"):
        raw_text = _extract_text_from_pdf(data)
    else:
        raw_text = data.decode("utf-8", errors="replace")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    try:
        parsed = await parse_syllabus_with_llm(raw_text, filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM parsing failed: {exc}")

    name = course_name.strip() or parsed.get("course_name") or filename
    course_id = _slugify(name)
    topics = parsed.get("topics", [])
    exam_hints = parsed.get("exam_hints", [])

    meta = save_syllabus(course_id, name, raw_text, topics, exam_hints)
    return JSONResponse({"ok": True, **meta})


@router.get("/list")
def list_syllabuses() -> JSONResponse:
    from ..services.syllabus import list_syllabuses as _list
    return JSONResponse({"syllabuses": _list()})


@router.delete("/{course_id}")
def delete_syllabus_route(course_id: str) -> JSONResponse:
    from ..services.syllabus import delete_syllabus
    deleted = delete_syllabus(course_id)
    return JSONResponse({"ok": deleted})
