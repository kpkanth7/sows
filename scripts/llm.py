"""LLM provider rotation (Phase 2.9, 2026-05-29).

Generalized chain across free OpenAI-compatible providers plus Gemini, so we
multiply the daily free ceiling 3-5×. Primary chosen via `LLM_PROVIDER`; on
failure / missing key we fall through every other provider that has a key set.

Providers tried (in order, missing keys skipped):
  1. groq        — Llama-3.3-70b, fast LPUs, generous free
  2. cerebras    — Llama-3.3-70b, very fast, free tier
  3. openrouter  — aggregator, several free Llama variants
  4. gemini      — gemini-2.0-flash, original default

All providers share `strip_json_fence` for downstream JSON parsing.
"""
import os
import logging
import time
import httpx
import google.generativeai as genai
from db import log_api_call

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
# Default rotation order (primary set via LLM_PROVIDER env moves to the front).
DEFAULT_CHAIN = ["groq", "cerebras", "openrouter", "gemini"]


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
    """Move the LLM_PROVIDER env (if set + known) to the front of the chain."""
    primary = os.environ.get("LLM_PROVIDER", "").lower().strip()
    chain = list(DEFAULT_CHAIN)
    if primary in chain:
        chain.remove(primary)
        chain.insert(0, primary)
    return chain


def _call_openai_compatible(provider: str, prompt: str, sb, max_tokens: int = None) -> str:
    cfg = OPENAI_COMPATIBLE[provider]
    api_key = os.environ.get(cfg["env"])
    if not api_key:
        raise RuntimeError(f"{cfg['env']} not set")
    model = os.environ.get("LLM_MODEL") or cfg["default_model"]
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
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.environ.get("LLM_MODEL") or "gemini-2.0-flash")
    max_retries = 5
    backoff = 10
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
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
