"""Syllabus tools for the execution agent."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "syllabus_list",
            "description": "List all uploaded course syllabuses. Returns course IDs, names, topic counts, and exam hints.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "syllabus_get",
            "description": "Get the full ordered topic list and exam hints from a specific course syllabus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "string",
                        "description": "Course ID from syllabus_list (e.g. 'cs-101').",
                    },
                },
                "required": ["course_id"],
                "additionalProperties": False,
            },
        },
    },
]


def get_schemas() -> List[Dict[str, Any]]:
    return _SCHEMAS


def syllabus_list() -> Dict[str, Any]:
    from server.services.syllabus import list_syllabuses
    return {"syllabuses": list_syllabuses()}


def syllabus_get(course_id: str) -> Dict[str, Any]:
    from server.services.syllabus import get_syllabus
    data = get_syllabus(course_id)
    if not data:
        return {"error": f"No syllabus found with ID '{course_id}'. Use syllabus_list to see available courses."}
    return data


def build_registry(agent_name: str) -> Dict[str, Callable[..., Any]]:  # noqa: ARG001
    return {
        "syllabus_list": syllabus_list,
        "syllabus_get": syllabus_get,
    }


__all__ = ["get_schemas", "build_registry"]
