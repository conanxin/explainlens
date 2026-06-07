"""OpenAI Images API transport — opt-in, fail-closed.

This module calls the OpenAI Images API (DALL-E) using ONLY the Python
standard library (urllib.request / urllib.error / json).

Safety rules:
- FAIL-CLOSED by default — allow_external_images must be explicitly True.
- ONLY the default OpenAI API base is allowed (no custom endpoints).
- Authorization header is set INSIDE the request, NEVER logged.
- api_key is NEVER printed, logged, or written to any file.
- Image prompts are NOT written to logs.
- Full API responses are NOT written to logs.
- No OpenAI SDK is imported or required.

Intended to be called by the OpenAIImageAdapter after explicit user opt-in:
    --image-adapter openai-image --allow-external-images
    AND OPENAI_API_KEY environment variable is set.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

# ── Constants ─────────────────────────────────────

_DEFAULT_API_BASE = "https://api.openai.com/v1"
_DEFAULT_TIMEOUT = 90.0
_DEFAULT_MODEL = "dall-e-3"
_DEFAULT_SIZE = "1024x1024"
_DEFAULT_QUALITY = "standard"

# ── Payload builders ──────────────────────────────


def build_openai_image_payload(
    prompt: str,
    model: str = _DEFAULT_MODEL,
    size: str = _DEFAULT_SIZE,
    quality: str = _DEFAULT_QUALITY,
    n: int = 1,
) -> dict:
    """Build the JSON-serializable payload for the OpenAI Images API.

    Args:
        prompt: Image generation prompt.
        model: Model name (e.g. "dall-e-3").
        size: Image size (e.g. "1024x1024").
        quality: Image quality ("standard" or "hd").
        n: Number of images to generate (1-10).

    Returns:
        Dict suitable for json.dumps() and sending as the request body.
    """
    return {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "quality": quality,
    }


# ── API Call ───────────────────────────────────────


def call_openai_images_api(
    prompt: str,
    api_key: str,
    *,
    model: str = _DEFAULT_MODEL,
    size: str = _DEFAULT_SIZE,
    quality: str = _DEFAULT_QUALITY,
    timeout_seconds: float = _DEFAULT_TIMEOUT,
    allow_external_images: bool = False,
    api_base: str = _DEFAULT_API_BASE,
) -> dict:
    """Call the OpenAI Images API and return the parsed response dict.

    Safety:
    - If allow_external_images=False, immediately raises RuntimeError.
    - If api_base is not the default, raises ValueError.
    - Authorization header is set inside the request object ONLY.
    - api_key is NEVER printed, logged, or written anywhere.
    - Image prompt is NOT written to logs.
    - Full response body is NOT written to logs.

    Args:
        prompt: Image generation prompt.
        api_key: OpenAI API key (read from env var OUTSIDE this function).
        model: Model name (default: "dall-e-3").
        size: Image size (default: "1024x1024").
        quality: Image quality (default: "standard").
        timeout_seconds: HTTP timeout (default 90s).
        allow_external_images: MUST be True for any network call to proceed.
        api_base: API base URL. MUST be the default OpenAI URL.

    Returns:
        Dict containing 'image_url', 'model', 'size' and 'adapter_notes'.

    Raises:
        RuntimeError: If allow_external_images=False or api_key is invalid.
        ValueError: If api_base is not the default.
        urllib.error.URLError: If the HTTP request fails.
        json.JSONDecodeError: If the response is not valid JSON.
    """
    # 1. Check allow_external_images — FAIL CLOSED
    if not allow_external_images:
        raise RuntimeError(
            "OpenAI Images API is fail-closed by default.\n"
            "To enable it, set OPENAI_API_KEY and pass --allow-external-images.\n"
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
    payload = build_openai_image_payload(prompt, model=model, size=size, quality=quality)
    endpoint = f"{api_base.rstrip('/')}/images/generations"

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
            f"OpenAI Images API HTTP {e.code} from {endpoint}. "
            f"Error body (first 300 chars): {body[:300]!r}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"OpenAI Images API network error: {e!r}. "
            f"No image was generated."
        ) from e

    # 7. Parse response JSON
    try:
        response_json = json.loads(response_body)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"OpenAI Images API returned invalid JSON. "
            f"Response body (first 300 chars): {response_body[:300]!r}",
            response_body,
            0,
        ) from e

    # 8. Extract image URL
    image_url = extract_image_url_from_response(response_json)

    return {
        "image_url": image_url,
        "model": model,
        "size": size,
        "adapter_notes": [
            f"OpenAI Images API: {model}",
            f"size: {size}",
            f"quality: {quality}",
        ],
    }


# ── Response Extraction ─────────────────────────────


def extract_image_url_from_response(response_json: dict) -> str:
    """Extract the image URL from OpenAI Images API response.

    Handles the standard DALL-E response format:
        {"data": [{"url": "https://...", ...}]}

    Args:
        response_json: The full JSON response from OpenAI Images API.

    Returns:
        The image URL string.

    Raises:
        ValueError: If the response format is unknown or no URL is found.
    """
    if "data" not in response_json:
        raise ValueError(
            f"Cannot extract image URL from OpenAI Images API response. "
            f"Known keys: {list(response_json.keys())}. "
            f"Expected 'data' key with a list of image objects."
        )

    data = response_json["data"]
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(
            f"OpenAI Images API response 'data' is empty or not a list."
        )

    first_image = data[0]
    if not isinstance(first_image, dict):
        raise ValueError(
            f"Image entry is not a dict. Type: {type(first_image).__name__}"
        )

    url = first_image.get("url")
    if not url or not isinstance(url, str):
        raise ValueError(
            f"Image entry missing 'url' or url is not a string. "
            f"Keys: {list(first_image.keys())}"
        )

    if not url.startswith("https://"):
        raise ValueError(
            f"Image URL does not start with https://. "
            f"URL (first 100 chars): {url[:100]!r}"
        )

    return url


# ── Image download helper ──────────────────────────


def download_image_from_url(image_url: str, timeout_seconds: float = 60.0) -> bytes:
    """Download an image from a URL and return raw bytes.

    Safety:
    - Only downloads from https:// URLs.
    - Does NOT store or log the URL in error messages.

    Args:
        image_url: The URL to download from.
        timeout_seconds: HTTP timeout.

    Returns:
        Raw image bytes.

    Raises:
        ValueError: If URL is not https://.
        urllib.error.URLError: If the download fails.
    """
    if not image_url.startswith("https://"):
        raise ValueError(
            f"Image download only supports https:// URLs. "
            f"Received scheme: {image_url.split('://')[0]}"
        )

    req = urllib.request.Request(
        image_url,
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise urllib.error.URLError(
            f"Failed to download image: HTTP {e.code}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Failed to download image: network error."
        ) from e


# ── Mock/Test helper ──────────────────────────────


def run_mock_openai_image_transport(prompt: str, model: str = _DEFAULT_MODEL) -> dict:
    """Mock OpenAI Images transport for testing — returns a placeholder result.

    Does NOT call any external API. Returns the same structure
    as call_openai_images_api() would for a successful call.

    The mock returns a data URI SVG placeholder with the prompt preview.

    Args:
        prompt: Image generation prompt (not used for image, but logged in notes).
        model: Model name (logged in notes only).

    Returns:
        Dict with 'image_url', 'model', 'size', 'adapter_notes'.
    """
    prompt_preview = prompt[:80] if len(prompt) > 80 else prompt

    return {
        "image_url": "",
        "model": model,
        "size": "1024x1024",
        "adapter_notes": [
            f"mock OpenAI Images transport: would call {model}",
            f"prompt preview: {prompt_preview}...",
            "NO real API call was made",
        ],
    }
