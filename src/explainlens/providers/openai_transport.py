"""OpenAI Responses API transport — opt-in, fail-closed.

This module calls the OpenAI Responses API using ONLY the Python
standard library (urllib.request / urllib.error / json).

Safety rules:
- FAIL-CLOSED by default — allow_external_api must be explicitly True.
- ONLY the default OpenAI API base is allowed (no custom endpoints).
- Authorization header is set INSIDE the request, NEVER logged.
- api_key is NEVER printed, logged, or written to any file.
- Prompt text is NOT written to logs.
- Full API responses are NOT written to logs.
- No OpenAI SDK is imported or required.

Intended to be called by the OpenAI provider after explicit user opt-in:
    --provider openai --allow-external-api
    AND OPENAI_API_KEY environment variable is set.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from explainlens.providers.fixture_transport import run_fixture_transport
from explainlens.providers.prompt_contract import ProviderPromptPack

# ── Constants ─────────────────────────────────────

_DEFAULT_API_BASE = "https://api.openai.com/v1"
_DEFAULT_TIMEOUT = 60.0

# ── Payload builders ──────────────────────────────

def build_openai_responses_payload(prompt_pack: ProviderPromptPack, model: str) -> dict:
    """Build the JSON-serializable payload for the OpenAI Responses API.

    Args:
        prompt_pack: The structured provider prompt pack.
        model: Model name (e.g. "gpt-5.5").

    Returns:
        Dict suitable for json.dumps() and sending as the request body.
    """
    system_text = _render_system_text(prompt_pack)
    user_text = _render_user_text(prompt_pack)

    return {
        "model": model,
        "input": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "explainlens_structured_output",
                    "schema": _build_output_schema(),
                    "strict": True,
                },
            },
        },
        "temperature": 0.2,
    }


def _render_system_text(prompt_pack: ProviderPromptPack) -> str:
    """Render the system instruction text from the prompt pack."""
    lines = [
        "You are an expert explainer. Your task is to analyze complex content",
        "and produce a structured explanation as valid JSON.",
        "",
        f"Audience level: {prompt_pack.audience_level}",
        f"Desired number of explanation cards: {prompt_pack.desired_card_count}",
        "",
        "Output contract (YOU MUST FOLLOW THIS EXACTLY):",
        json.dumps(prompt_pack.output_contract, indent=2, ensure_ascii=False),
        "",
        "Safety rules (YOU MUST FOLLOW THESE):",
    ]
    for rule in prompt_pack.safety_rules:
        lines.append(f"- {rule}")
    lines += [
        "",
        "You MUST include 'source_chunk_ids' in every card.",
        "Every source_chunk_id MUST be a chunk_id from the provided source chunks.",
        "Do NOT invent chunk IDs. Do NOT use numeric indices only.",
    ]
    return "\n".join(lines)


def _render_user_text(prompt_pack: ProviderPromptPack) -> str:
    """Render the user message with source chunks."""
    lines = [
        f"Task: {prompt_pack.task}",
        f"Source type: {prompt_pack.source_type}",
        "",
        "Source chunks:",
    ]
    for chunk in prompt_pack.source_chunks:
        chunk_lines = [
            f"  [{chunk.chunk_id}]",
        ]
        if chunk.page_start is not None:
            page_info = f"page {chunk.page_start}"
            if chunk.page_end is not None and chunk.page_end != chunk.page_start:
                page_info = f"pages {chunk.page_start}-{chunk.page_end}"
            chunk_lines.append(f"    ({page_info})")
        text = chunk.text[:2000] if len(chunk.text) > 2000 else chunk.text
        chunk_lines.append(f"    Text: {text}")
        lines.extend(chunk_lines)
    lines += [
        "",
        f"Please produce exactly {prompt_pack.desired_card_count} explanation cards",
        "following the output contract specified in the system instructions.",
        "Return ONLY valid JSON matching the contract — no markdown fences, no extra text.",
    ]
    return "\n".join(lines)


def _build_output_schema() -> dict:
    """Build the JSON Schema for structured output."""
    return {
        "type": "object",
        "properties": {
            "concept_map": {
                "type": "object",
                "properties": {
                    "core_problem": {"type": "string"},
                    "key_concepts": {"type": "array", "items": {"type": "string"}},
                    "key_claims": {"type": "array", "items": {"type": "string"}},
                    "methods_or_mechanisms": {"type": "array", "items": {"type": "string"}},
                    "evidence_or_examples": {"type": "array", "items": {"type": "string"}},
                    "limitations": {"type": "array", "items": {"type": "string"}},
                    "why_it_matters": {"type": "string"},
                },
                "required": ["core_problem", "key_concepts", "key_claims"],
            },
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "explanation": {"type": "string"},
                        "visual_metaphor": {"type": "string"},
                        "visual_scene": {"type": "string"},
                        "takeaway": {"type": "string"},
                        "source_chunk_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["title", "explanation", "source_chunk_ids"],
                },
            },
            "provider_notes": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["concept_map", "cards"],
        "additionalProperties": False,
    }


# ── API Call ───────────────────────────────────────

def call_openai_responses_api(
    prompt_pack: ProviderPromptPack,
    model: str,
    api_key: str,
    timeout_seconds: float = _DEFAULT_TIMEOUT,
    allow_external_api: bool = False,
    api_base: str = _DEFAULT_API_BASE,
) -> dict:
    """Call the OpenAI Responses API and return the parsed response dict.

    Safety:
    - If allow_external_api=False, immediately raises RuntimeError.
    - If api_base is not the default, raises ValueError.
    - Authorization header is set inside the request object ONLY.
    - api_key is NEVER printed, logged, or written anywhere.
    - No prompt text is written to logs.
    - Full response body is NOT written to logs (only parsed fields).

    Args:
        prompt_pack: The structured prompt pack.
        model: Model name (e.g. "gpt-5.5").
        api_key: OpenAI API key (read from env var OUTSIDE this function).
        timeout_seconds: HTTP timeout (default 60s).
        allow_external_api: MUST be True for any network call to proceed.
        api_base: API base URL. MUST be the default OpenAI URL.

    Returns:
        Dict containing 'concept_map', 'cards', and 'provider_notes'.

    Raises:
        RuntimeError: If allow_external_api=False or api_key is invalid.
        ValueError: If api_base is not the default.
        urllib.error.URLError: If the HTTP request fails.
        json.JSONDecodeError: If the response is not valid JSON.
        ValueError: If the response format is unknown or content is invalid.
    """
    # 1. Check allow_external_api — FAIL CLOSED
    if not allow_external_api:
        raise RuntimeError(
            "OpenAI provider is fail-closed by default.\n"
            "To enable it, set OPENAI_API_KEY and pass --allow-external-api.\n"
            "No request was sent."
        )

    # 2. Validate api_key (never print it)
    if not api_key or not isinstance(api_key, str):
        raise RuntimeError(
            "OPENAI_API_KEY is not set.\n"
            "No request was sent."
        )
    if not (api_key.startswith("sk-") or api_key.startswith("ssk-")):
        raise RuntimeError(
            "OPENAI_API_KEY does not look valid "
            "(should start with sk- or sk-proj-).\n"
            "No request was sent."
        )

    # 3. Validate api_base — ONLY default allowed in this phase
    if api_base != _DEFAULT_API_BASE:
        raise ValueError(
            f"Custom api_base is not supported in this version.\n"
            f"Allowed api_base: {_DEFAULT_API_BASE}\n"
            f"Received: {api_base}"
        )

    # 4. Build payload (no API call yet)
    payload = build_openai_responses_payload(prompt_pack, model)
    endpoint = f"{api_base.rstrip('/')}/responses"

    # 5. Build request with Authorization header
    # CRITICAL: header is set INSIDE the request object.
    # DO NOT print, log, or store the request headers anywhere.
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    # 6. Make HTTP request
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            response_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        # DO NOT include api_key in error messages
        raise urllib.error.URLError(
            f"OpenAI API HTTP {e.code} from {endpoint}. "
            f"Error body (first 300 chars): {body[:300]!r}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"OpenAI API network error: {e!r}. "
            f"No output was generated."
        ) from e

    # 7. Parse response JSON
    try:
        response_json = json.loads(response_body)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"OpenAI API returned invalid JSON. "
            f"Response body (first 300 chars): {response_body[:300]!r}",
            response_body,
            0,
        ) from e

    # 8. Extract structured response
    extracted = extract_structured_response_from_openai_json(response_json)

    # 9. Validate against response contract
    from explainlens.providers.response_contract import parse_provider_response
    from explainlens.schemas import SourceChunk

    chunks = [
        SourceChunk(
            chunk_id=c.chunk_id,
            text=c.text,
            start_char=0,
            end_char=len(c.text),
            source_type=prompt_pack.source_type,
            page_start=c.page_start,
            page_end=c.page_end,
        )
        for c in prompt_pack.source_chunks
    ]
    validated = parse_provider_response(extracted, chunks)

    return {
        "concept_map": validated.concept_map.model_dump(),
        "cards": [c.model_dump() for c in validated.cards],
        "provider_notes": validated.provider_notes + [
            f"OpenAI Responses API: {model}",
            f"endpoint: {endpoint}",
        ],
    }


# ── Response Extraction ─────────────────────────────

def extract_structured_response_from_openai_json(response_json: dict) -> dict:
    """Extract the structured response dict from OpenAI API JSON.

    Handles two response shapes:

    Form A — direct output_text:
        {"output_text": '{"concept_map": ..., "cards": ...}'}

    Form B — output list with content text:
        {"output": [{"content": [{"type": "output_text", "text": "..."}]}]}

    Args:
        response_json: The full JSON response from OpenAI API.

    Returns:
        Dict with 'concept_map', 'cards', 'provider_notes'.

    Raises:
        ValueError: If the response format is unknown or content is not valid JSON.
    """
    # Form A: output_text (Responses API direct JSON mode)
    if "output_text" in response_json:
        raw_text = response_json["output_text"]
        if not isinstance(raw_text, str):
            raise ValueError(
                f"OpenAI response 'output_text' is not a string. "
                f"Type: {type(raw_text).__name__}"
            )
        try:
            structured = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"OpenAI response 'output_text' is not valid JSON. "
                f"Content (first 200 chars): {raw_text[:200]!r}. "
                f"Error: {e}"
            ) from e
        return _validate_extracted_structure(structured)

    # Form B: output list (Responses API with output items)
    if "output" in response_json and isinstance(response_json["output"], list):
        for item in response_json["output"]:
            if not isinstance(item, dict):
                continue
            content_list = item.get("content", [])
            if not isinstance(content_list, list):
                continue
            for content_item in content_list:
                if not isinstance(content_item, dict):
                    continue
                if content_item.get("type") == "output_text":
                    raw_text = content_item.get("text", "")
                    if not raw_text:
                        continue
                    try:
                        structured = json.loads(raw_text)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"OpenAI response output content is not valid JSON. "
                            f"Content (first 200 chars): {raw_text[:200]!r}. "
                            f"Error: {e}"
                        ) from e
                    return _validate_extracted_structure(structured)

    # Unknown format
    raise ValueError(
        f"Cannot extract structured response from OpenAI API response. "
        f"Known keys: {list(response_json.keys())}. "
        f"Expected 'output_text' or 'output' with content items."
    )


def _validate_extracted_structure(structured: dict) -> dict:
    """Validate that the extracted structure has required keys.

    Args:
        structured: Parsed dict from OpenAI response.

    Returns:
        The same dict (validated).

    Raises:
        ValueError: If required keys are missing or structure is invalid.
    """
    if not isinstance(structured, dict):
        raise ValueError(
            f"Extracted response is not a dict. Type: {type(structured).__name__}"
        )

    if "concept_map" not in structured:
        raise ValueError(
            f"Extracted response missing 'concept_map'. "
            f"Keys: {list(structured.keys())}"
        )

    if "cards" not in structured:
        raise ValueError(
            f"Extracted response missing 'cards'. "
            f"Keys: {list(structured.keys())}"
        )

    if not isinstance(structured["cards"], list):
        raise ValueError(
            f"Extracted 'cards' is not a list. "
            f"Type: {type(structured['cards']).__name__}"
        )

    # Check each card has source_chunk_ids
    for i, card in enumerate(structured["cards"]):
        if not isinstance(card, dict):
            raise ValueError(
                f"Card {i} is not a dict. Type: {type(card).__name__}"
            )
        if "source_chunk_ids" not in card:
            raise ValueError(
                f"Card {i} ('{card.get('title', '?')}') "
                f"missing 'source_chunk_ids'."
            )

    return structured


# ── Mock/Test helper ──────────────────────────────

def run_mock_openai_transport(prompt_pack: ProviderPromptPack, model: str) -> dict:
    """Mock OpenAI transport for testing — uses fixture output.

    Does NOT call any external API. Returns the same structure
    as call_openai_responses_api() would for a successful call.

    Args:
        prompt_pack: The structured prompt pack.
        model: Model name (not used in mock).

    Returns:
        Dict with 'concept_map', 'cards', 'provider_notes'.
    """
    fixture_result = run_fixture_transport(prompt_pack)
    fixture_result.setdefault("provider_notes", [])
    fixture_result["provider_notes"].append(
        f"mock OpenAI transport: would call {model}"
    )
    fixture_result["provider_notes"].append(
        "NO real API call was made"
    )
    return fixture_result
