import os
import logging
import time
import httpx
import google.generativeai as genai
from db import log_api_call

logger = logging.getLogger(__name__)


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


def generate_llm_content(prompt: str, sb, max_tokens: int = None) -> str:
    """Generate text via the configured LLM provider.

    Provider chosen by LLM_PROVIDER env (default 'gemini'). Groq is tried first
    when selected and falls back to Gemini on missing key or API error. Gemini
    retries with exponential backoff on rate limits.
    """
    provider = os.environ.get('LLM_PROVIDER', 'gemini').lower()
    model_name = os.environ.get('LLM_MODEL')

    if provider == 'groq':
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            logger.warning("GROQ_API_KEY not set, falling back to gemini")
            provider = 'gemini'
        else:
            model = model_name or 'llama-3.3-70b-versatile'
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
                if max_tokens:
                    payload["max_tokens"] = max_tokens

                resp = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload, headers=headers, timeout=60
                )
                resp.raise_for_status()
                log_api_call(sb, 'gemini', 1)  # Share tracking metric
                return resp.json()['choices'][0]['message']['content']
            except Exception as e:
                logger.error(f"Groq API error: {e}, falling back to gemini")
                provider = 'gemini'

    if provider == 'gemini':
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise Exception("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name or 'gemini-2.0-flash')

        max_retries = 5
        backoff = 10
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                log_api_call(sb, 'gemini', 1)
                return response.text
            except Exception as e:
                err_msg = str(e)
                if '429' in err_msg or 'ResourceExhausted' in err_msg or 'Quota exceeded' in err_msg:
                    if attempt < max_retries - 1:
                        logger.warning(f"Gemini API rate limit hit. Sleeping for {backoff}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(backoff)
                        backoff *= 2
                    else:
                        raise e
                else:
                    raise e

    raise Exception(f"Unsupported LLM provider: {provider}")
