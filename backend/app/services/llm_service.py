import httpx
import json
import logging
from abc import ABC, abstractmethod
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMService(ABC):
    @abstractmethod
    async def summarize_trends(self, trends: list[dict]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def explain_entity_trend(self, entity_name: str, signals: list[dict]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def compare_entities(self, left: str, right: str, signals: list[dict]) -> str:
        raise NotImplementedError


class OllamaService(LLMService):
    """Local LLM service using Ollama."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "http://localhost:11434/api/generate"
        self.model = self.settings.llm_model

    async def _generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.base_url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return f"[LLM Error: {e}]"

    async def summarize_trends(self, trends: list[dict]) -> str:
        if not trends:
            return "No trend data available for summarization."
        prompt = f"Summarize the following technology trends based on recent activity signals: {json.dumps(trends)}. Provide a concise intelligence brief."
        return await self._generate(prompt)

    async def explain_entity_trend(self, entity_name: str, signals: list[dict]) -> str:
        if not signals:
            return f"No signal data available for {entity_name}."
        prompt = f"Explain why {entity_name} is trending based on these recent signals: {json.dumps(signals)}. Be concise."
        return await self._generate(prompt)

    async def compare_entities(self, left: str, right: str, signals: list[dict]) -> str:
        prompt = f"Compare the trend momentum of {left} and {right} based on these signals: {json.dumps(signals)}. Which one has stronger developer interest?"
        return await self._generate(prompt)


class LocalLLMService(LLMService):
    """Deterministic local fallback used until a hosted provider is configured."""

    async def summarize_trends(self, trends: list[dict]) -> str:
        if not trends:
            return "No strong live trend signal has been collected yet."
        names = ", ".join(item.get("entity_name", "unknown") for item in trends[:5])
        return f"Current live signals are strongest around {names}. Activity is based on source mentions, item volume, and engagement."

    async def explain_entity_trend(self, entity_name: str, signals: list[dict]) -> str:
        if not signals:
            return f"{entity_name} does not have enough recent signal yet for a confident explanation."
        sources = sorted({item.get("source_name", "unknown") for item in signals})
        return f"{entity_name} is trending across {', '.join(sources)} based on recent mentions and engagement-weighted activity."

    async def compare_entities(self, left: str, right: str, signals: list[dict]) -> str:
        left_score = sum(item.get("trend_score", 0) for item in signals if item.get("entity_name") == left)
        right_score = sum(item.get("trend_score", 0) for item in signals if item.get("entity_name") == right)
        leader = left if left_score >= right_score else right
        return f"{leader} currently has the stronger short-term signal based on collected source activity."

class GeminiService(LLMService):
    """LLM service using Google Gemini."""

    def __init__(self):
        self.settings = get_settings()
        import google.generativeai as genai
        import os
        api_key = os.environ.get("GEMINI_API_KEY", getattr(self.settings, "gemini_api_key", ""))
        genai.configure(api_key=api_key)
        
        model_name = getattr(self.settings, "llm_model", "")
        if not model_name or model_name == "llama3":
            model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(model_name)

    async def _generate(self, prompt: str) -> str:
        try:
            # Note: run in executor if async is required or natively support generate_content_async
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"[LLM Error: {e}]"

    async def summarize_trends(self, trends: list[dict]) -> str:
        if not trends:
            return "No trend data available for summarization."
        prompt = f"Summarize the following technology trends based on recent activity signals: {json.dumps(trends)}. Provide a concise intelligence brief."
        return await self._generate(prompt)

    async def explain_entity_trend(self, entity_name: str, signals: list[dict]) -> str:
        if not signals:
            return f"No signal data available for {entity_name}."
        prompt = f"Explain why {entity_name} is trending based on these recent signals: {json.dumps(signals)}. Be concise."
        return await self._generate(prompt)

    async def compare_entities(self, left: str, right: str, signals: list[dict]) -> str:
        prompt = f"Compare the trend momentum of {left} and {right} based on these signals: {json.dumps(signals)}. Which one has stronger developer interest?"
        return await self._generate(prompt)

def get_llm_service() -> LLMService:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        logger.info(f"Using Ollama with model: {settings.llm_model}")
        return OllamaService()
    elif settings.llm_provider == "gemini":
        logger.info("Using Gemini")
        return GeminiService()
    
    logger.info("Using local provider-agnostic LLM fallback. Configure LLM_PROVIDER to add a hosted provider.")
    return LocalLLMService()
