# backend/reasoning/schemas.py
"""JSON Schemas for OpenAI structured outputs — replaces v1's regex JSON scraping."""

HS6_SCHEMA = {
    "name": "hs6_selection",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "code": {"type": "string"},
            "explanation": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "gri_applied": {"type": "string"},
            "alternatives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "code": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["code", "reason"],
                },
            },
        },
        "required": ["code", "explanation", "confidence", "gri_applied", "alternatives"],
    },
}

HS10_SCHEMA = {
    "name": "hs10_suggestions",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "code": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                        "explanation": {"type": "string"},
                        "gri_applied": {"type": "string"},
                        "bti_reference": {"type": ["string", "null"]},
                    },
                    "required": ["code", "confidence", "explanation",
                                 "gri_applied", "bti_reference"],
                },
            },
            "ambiguous": {"type": "boolean"},
            "ambiguity_note": {"type": ["string", "null"]},
        },
        "required": ["suggestions", "ambiguous", "ambiguity_note"],
    },
}

QUESTIONS_SCHEMA = {
    "name": "narrowing_questions",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "question": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "discriminator_key": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                    },
                    "required": ["question", "options", "discriminator_key", "why_it_matters"],
                },
            }
        },
        "required": ["questions"],
    },
}
