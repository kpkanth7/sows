"""LLM provider rotation (Phase 2.9, 2026-05-29).

Generalized chain across free OpenAI-compatible providers plus Gemini, so we
multiply the daily free ceiling 3-5×. Primary chosen via `LLM_PROVIDER`; on
failure / missing key we fall through every other provider that has a key set.

Providers tried (in order, missing keys skipped):
  1. groq        — primary free-tier provider
  2. gemini      — fallback provider

Set `LLM_PROVIDER_CHAIN` to a comma-separated list if you want to opt into
additional providers such as cerebras or openrouter.

All providers share `strip_json_fence` for downstream JSON parsing.
"""
import os
import logging
import time
import httpx
from db import log_api_call, check_quota

logger = logging.getLogger(__name__)


# OpenAI-compatible provider config. Order = default chain.
OPENAI_COMPATIBLE = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "env": "CEREBRAS_API_KEY",
        "default_model": "llama-3.3-70b",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "env": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
    },
}
# Default rotation order. Keep the chain short unless you explicitly opt in to
# more providers via LLM_PROVIDER_CHAIN.
DEFAULT_CHAIN = ["groq", "gemini"]


def strip_json_fence(text: str) -> str:
    """Strip a markdown code fence (```json ... ``` or ``` ... ```) from LLM output.

    Returns the inner payload trimmed of surrounding whitespace. Safe on plain
    (unfenced) text and on None/empty input.
    """
    if not text:
        return text or ""
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()


def _resolve_chain():
    """Resolve provider order.

    Default behavior is Groq first, Gemini second. If LLM_PROVIDER_CHAIN is set,
    it replaces the default chain. LLM_PROVIDER (if set) is promoted to the
    front when it matches a known provider.
    """
    raw_chain = os.environ.get("LLM_PROVIDER_CHAIN", "").strip()
    if raw_chain:
        chain = [part.strip().lower() for part in raw_chain.split(",") if part.strip()]
    else:
        chain = list(DEFAULT_CHAIN)
    primary = os.environ.get("LLM_PROVIDER", "").lower().strip()
    if primary in chain:
        chain.remove(primary)
        chain.insert(0, primary)
    return chain


def get_primary_provider() -> str:
    """Return the first provider in the resolved chain."""
    chain = _resolve_chain()
    return chain[0] if chain else "gemini"


def has_llm_capacity(sb, cost: int = 1) -> bool:
    """True when at least one configured provider is still under quota."""
    for provider in _resolve_chain():
        key = None
        if provider == "gemini":
            key = os.environ.get("GEMINI_API_KEY")
        elif provider in OPENAI_COMPATIBLE:
            key = os.environ.get(OPENAI_COMPATIBLE[provider]["env"])
        if not key:
            continue
        if check_quota(sb, provider, cost):
            return True
    return False


def _resolve_openai_model(provider: str, cfg: dict) -> str:
    """Pick a model for OpenAI-compatible providers.

    LLM_MODEL is treated as a shared override, but Gemini-style model names are
    ignored for non-Gemini providers so one bad env var cannot poison every
    provider in the chain.
    """
    override = (os.environ.get("LLM_MODEL") or "").strip()
    if override:
        if override.startswith("gemini"):
            logger.warning(
                "Ignoring Gemini-style LLM_MODEL override '%s' for provider %s; using provider default %s",
                override,
                provider,
                cfg["default_model"],
            )
        else:
            return override
    return cfg["default_model"]


def _call_openai_compatible(provider: str, prompt: str, sb, max_tokens: int = None) -> str:
    cfg = OPENAI_COMPATIBLE[provider]
    api_key = os.environ.get(cfg["env"])
    if not api_key:
        raise RuntimeError(f"{cfg['env']} not set")
    model = _resolve_openai_model(provider, cfg)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    resp = httpx.post(
        cfg["url"],
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    log_api_call(sb, provider, 1)
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(prompt: str, sb, max_tokens: int = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai

    client = genai.Client(api_key=api_key)
    llm_model = os.environ.get("LLM_MODEL", "")
    model = os.environ.get("GEMINI_MODEL") or (
        llm_model if llm_model.startswith("gemini") else "gemini-2.0-flash"
    )
    max_retries = 5
    backoff = 10
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            log_api_call(sb, "gemini", 1)
            return response.text
        except Exception as e:
            msg = str(e)
            if ("429" in msg or "ResourceExhausted" in msg or "Quota exceeded" in msg) and attempt < max_retries - 1:
                logger.warning(f"Gemini rate-limited; sleep {backoff}s ({attempt + 1}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2
            else:
                raise


def _call_provider(provider: str, prompt: str, sb, max_tokens: int = None) -> str:
    if provider == "gemini":
        return _call_gemini(prompt, sb, max_tokens)
    if provider in OPENAI_COMPATIBLE:
        return _call_openai_compatible(provider, prompt, sb, max_tokens)
    raise RuntimeError(f"Unknown provider: {provider}")


def generate_llm_content(prompt: str, sb, max_tokens: int = None) -> str:
    """Try the configured chain of providers; first success wins.

    Skips providers whose API key is missing. Logs and falls through on any
    failure. Raises only if every provider in the chain fails.
    """
    last_err = None
    for provider in _resolve_chain():
        try:
            return _call_provider(provider, prompt, sb, max_tokens)
        except Exception as e:
            logger.warning(f"LLM provider '{provider}' failed: {e} — trying next")
            last_err = e
            continue
    raise RuntimeError(f"All LLM providers failed. Last error: {last_err}")
