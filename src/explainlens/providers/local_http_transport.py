"""Local HTTP transport — loopback-only HTTP client for local model providers.

This module handles sending prompts to, and receiving responses from,
localhost-only HTTP endpoints (Ollama, LM Studio, llama.cpp server,
or any OpenAI-compatible local endpoint).

Safety rules:
- ONLY loopback endpoints are allowed (localhost, 127.0.0.1, ::1)
- NO remote HTTP (no https://, no LAN addresses)
- NO API keys are read or sent
- NO Authorization headers are set
- Network calls require explicit opt-in (allow_network=True)
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Literal, Optional

from explainlens.providers.prompt_contract import ProviderPromptPack
from explainlens.providers.response_contract import (
    ProviderCardResponse,
    ProviderConceptMapResponse,
    ProviderStructuredResponse,
    parse_provider_response,
)
from explainlens.providers.fixture_transport import run_fixture_transport

# ── Protocol type ───────────────────────────────────────────────

ProtocolType = Literal["fixture", "ollama-chat", "openai-compatible-chat"]

# ── Endpoint validation ─────────────────────────────────────────

_ALLOWED_LOOPBACK = {
    "localhost",
    "127.0.0.1",
    "::1",
    "[::1]",
}


def is_local_endpoint(url: str) -> bool:
    """Check if a URL is a loopback-only endpoint.

    Allowed:
        http://localhost:...
        http://127.0.0.1:...
        http://[::1]:...

    Rejected:
        https://... (any HTTPS)
        http://example.com/...
        http://192.168.x.x/...
        http://10.x.x.x/...
        http://172.16.x.x/...
        Any empty or malformed URL

    Args:
        url: The URL to check.

    Returns:
        True if the URL is a loopback endpoint, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False

    url_stripped = url.strip()

    # Must start with http:// (no https)
    if not url_stripped.startswith("http://"):
        return False

    # Extract host part
    # http://[host]:port/path or http://host:port/path
    rest = url_stripped[len("http://"):]
    # Remove path
    host_port = rest.split("/")[0].lower()

    # Extract host from host:port, handling IPv6 brackets
    if host_port.startswith("["):
        # IPv6: [...] or [...]:port
        end_bracket = host_port.find("]")
        if end_bracket != -1:
            host_part = host_port[1:end_bracket]
        else:
            return False  # Malformed IPv6
    else:
        # IPv4 or hostname
        host_part = host_port.split(":")[0]

    return host_part in _ALLOWED_LOOPBACK


def _resolve_hostname(hostname: str) -> set[str]:
    """Resolve a hostname to IP addresses for additional safety check."""
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return {info[4][0] for info in results}
    except socket.gaierror:
        return set()


def is_safe_endpoint(url: str) -> tuple[bool, str]:
    """Extended safety check: validate URL and resolve to confirm loopback.

    Args:
        url: The URL to check.

    Returns:
        (is_safe, reason) tuple.
    """
    if not is_local_endpoint(url):
        return False, f"URL is not a recognized loopback endpoint: {url}"

    # Additional: resolve to check for DNS rebinding attacks
    rest = url.strip()[len("http://"):]
    host_part = rest.split("/")[0].split(":")[0].lower()

    if host_part in ("localhost",):
        # Resolve localhost to confirm it maps to loopback
        try:
            ips = _resolve_hostname(host_part)
            loopback_ips = {"127.0.0.1", "::1", "0:0:0:0:0:0:0:1", "0:0:0:0:0:0:0:1%0"}
            if not ips.intersection(loopback_ips):
                return False, f"localhost resolved to non-loopback IPs: {ips}"
        except Exception:
            pass  # If resolution fails, still allow (offline scenarios)

    return True, "OK"


# ── Payload builders ───────────────────────────────────────────

def _build_ollama_chat_payload(prompt_pack: ProviderPromptPack, model: str) -> dict:
    """Build Ollama /api/chat-compatible payload.

    Reference: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-response

    Args:
        prompt_pack: The structured prompt pack.
        model: Model name (e.g., "llama3.2").

    Returns:
        Dict suitable for JSON-serialization as Ollama chat request.
    """
    system_prompt = _render_system_prompt(prompt_pack)
    user_prompt = _render_user_prompt(prompt_pack)

    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
        },
    }


def _build_openai_compatible_chat_payload(prompt_pack: ProviderPromptPack, model: str) -> dict:
    """Build OpenAI-compatible /v1/chat/completions payload.

    Args:
        prompt_pack: The structured prompt pack.
        model: Model name (e.g., "local-model").

    Returns:
        Dict suitable for JSON-serialization as OpenAI-compatible request.
    """
    system_prompt = _render_system_prompt(prompt_pack)
    user_prompt = _render_user_prompt(prompt_pack)

    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }


def _render_system_prompt(prompt_pack: ProviderPromptPack) -> str:
    """Render the system prompt from the prompt pack."""
    lines = [
        "You are an expert explainer. Your task is to analyze complex content",
        "and produce a structured explanation.",
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
        "Source chunks are provided in the user message. You MUST reference",
        "chunk IDs in your response using the 'source_chunk_ids' field.",
    ]
    return "\n".join(lines)


def _render_user_prompt(prompt_pack: ProviderPromptPack) -> str:
    """Render the user prompt with source chunks."""
    lines = [
        f"Task: {prompt_pack.task}",
        f"Source type: {prompt_pack.source_type}",
        "",
        "Source chunks:",
    ]
    for i, chunk in enumerate(prompt_pack.source_chunks):
        chunk_lines = [
            f"  [{chunk.chunk_id}]",
        ]
        if chunk.page_start is not None:
            page_info = f"page {chunk.page_start}"
            if chunk.page_end is not None and chunk.page_end != chunk.page_start:
                page_info = f"pages {chunk.page_start}-{chunk.page_end}"
            chunk_lines.append(f"    ({page_info})")
        chunk_lines.append(f"    Text: {chunk.text[:300]}")
        lines.extend(chunk_lines)
    lines += [
        "",
        f"Please produce exactly {prompt_pack.desired_card_count} explanation cards",
        "following the output contract specified in the system prompt.",
        "Return ONLY valid JSON matching the contract — no markdown fences, no extra text.",
    ]
    return "\n".join(lines)


def build_local_http_payload(
    prompt_pack: ProviderPromptPack,
    model: str,
    protocol: ProtocolType,
) -> dict:
    """Build the HTTP request payload for the given protocol.

    Args:
        prompt_pack: The structured prompt pack.
        model: Model identifier string.
        protocol: Protocol type ("fixture", "ollama-chat", "openai-compatible-chat").

    Returns:
        Dict payload for the specific protocol.

    Raises:
        ValueError: If protocol is not supported.
    """
    if protocol == "fixture":
        # Fixture protocol doesn't use HTTP — return a marker
        return {"__fixture__": True, "model": model}
    elif protocol == "ollama-chat":
        return _build_ollama_chat_payload(prompt_pack, model)
    elif protocol == "openai-compatible-chat":
        return _build_openai_compatible_chat_payload(prompt_pack, model)
    else:
        raise ValueError(
            f"Unsupported protocol: {protocol}. "
            "Supported: fixture, ollama-chat, openai-compatible-chat"
        )


# ── HTTP call ──────────────────────────────────────────────────

def call_local_http_provider(
    prompt_pack: ProviderPromptPack,
    endpoint: str,
    model: str,
    protocol: ProtocolType,
    timeout_seconds: float = 30.0,
    allow_network: bool = False,
) -> dict:
    """Call a local HTTP provider and return the parsed response dict.

    Safety:
    - If allow_network=False, immediately raises RuntimeError without sending request.
    - If endpoint is not loopback, immediately raises ValueError.
    - No API keys are read or sent.
    - No Authorization header is set.

    Args:
        prompt_pack: The structured prompt pack.
        endpoint: The HTTP endpoint URL.
        model: Model name to use.
        protocol: Protocol type.
        timeout_seconds: HTTP timeout (default 30s).
        allow_network: Must be True for any HTTP call to proceed.

    Returns:
        Dict containing 'concept_map', 'cards', and 'provider_notes'.

    Raises:
        RuntimeError: If allow_network=False.
        ValueError: If endpoint is not a loopback address.
        urllib.error.URLError: If the HTTP request fails.
        json.JSONDecodeError: If the response is not valid JSON.
        ValidationError: If the response fails contract validation.
    """
    # 1. Handle fixture protocol (no HTTP, no network check needed)
    if protocol == "fixture":
        return run_fixture_transport(prompt_pack)

    # 2. Check allow_network
    if not allow_network:
        raise RuntimeError(
            "Local HTTP provider requires explicit network opt-in. "
            "Use --allow-local-http flag, or use --local-http-protocol fixture "
            "for offline testing."
        )

    # 3. Validate endpoint
    if not endpoint or not isinstance(endpoint, str):
        raise ValueError("Endpoint must be a non-empty string.")

    safe, reason = is_safe_endpoint(endpoint)
    if not safe:
        raise ValueError(
            f"Endpoint safety check failed: {reason}. "
            "Only loopback endpoints (localhost, 127.0.0.1, ::1) are allowed."
        )

    # 4. Build payload
    payload = build_local_http_payload(prompt_pack, model, protocol)

    # 5. Make HTTP request (no Authorization header, no API key)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            response_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        raise urllib.error.URLError(
            f"HTTP {e.code} from {endpoint}: {body}"
        ) from e
    except urllib.error.URLError:
        raise

    # 6. Parse response
    try:
        raw_response = json.loads(response_body)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON response from {endpoint}. "
            f"Response body (first 200 chars): {response_body[:200]!r}",
            response_body,
            0,
        ) from e

    # 7. Extract structured response from chat-format JSON
    extracted = extract_structured_response_from_chat_json(raw_response, protocol)

    # 8. Validate against response contract
    # (Need chunks for chunk_id validation — get from prompt_pack)
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
            f"local HTTP transport: {protocol} to {endpoint}",
            f"model: {model}",
        ],
    }


# ── Response extraction ─────────────────────────────────────────

def extract_structured_response_from_chat_json(
    response_json: dict,
    protocol: ProtocolType,
) -> dict:
    """Extract structured response from chat-format JSON.

    Handles:
    - Ollama-like: {"message": {"content": "{...}"}}
    - OpenAI-compatible: {"choices": [{"message": {"content": "{...}"}}]}

    Args:
        response_json: The raw JSON response dict.
        protocol: The protocol type (for error context).

    Returns:
        Dict with 'concept_map', 'cards', 'provider_notes'.

    Raises:
        ValueError: If the response format is unknown or content is not valid JSON.
    """
    content_str = _extract_content_string(response_json, protocol)

    if not content_str:
        raise ValueError(
            f"Could not extract content string from {protocol} response. "
            f"Response keys: {list(response_json.keys())}"
        )

    # Try to parse content as JSON
    try:
        structured = json.loads(content_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Provider response content is not valid JSON. "
            f"Protocol: {protocol}. "
            f"Content (first 200 chars): {content_str[:200]!r}. "
            f"Error: {e}"
        ) from e

    # Validate expected keys
    if "concept_map" not in structured:
        raise ValueError(
            f"Provider response missing 'concept_map'. "
            f"Keys: {list(structured.keys())}"
        )
    if "cards" not in structured:
        raise ValueError(
            f"Provider response missing 'cards'. "
            f"Keys: {list(structured.keys())}"
        )

    return structured


def _extract_content_string(response_json: dict, protocol: ProtocolType) -> Optional[str]:
    """Extract the content string from various response formats."""
    # Ollama format: {"message": {"content": "..."}}
    if "message" in response_json:
        msg = response_json["message"]
        if isinstance(msg, dict) and "content" in msg:
            return msg["content"]

    # OpenAI-compatible format: {"choices": [{"message": {"content": "..."}}]}
    if "choices" in response_json:
        choices = response_json["choices"]
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                msg = first.get("message", {})
                if isinstance(msg, dict):
                    return msg.get("content")

    # Raw content field (some local servers)
    if "content" in response_json:
        return response_json["content"]

    # Raw response field
    if "response" in response_json:
        return response_json["response"]

    return None
