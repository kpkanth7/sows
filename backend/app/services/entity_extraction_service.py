import re
from dataclasses import dataclass

from backend.app.utils.text_utils import canonicalize_name


@dataclass(frozen=True)
class ExtractedEntity:
    name: str
    entity_type: str
    canonical_name: str


TECH_TERMS: tuple[str, ...] = (
    "Python",
    "JavaScript",
    "TypeScript",
    "React",
    "Next.js",
    "FastAPI",
    "PostgreSQL",
    "Kafka",
    "LangGraph",
    "LangChain",
    "Docker",
    "Kubernetes",
    "Rust",
    "Go",
    "Swift",
    "Linux",
    "OpenAI",
    "Mistral",
    "Qwen",
    "TimesFM",
    "Hugging Face",
    "PyTorch",
    "TensorFlow",
    "RAG",
    "LLM",
    "AI agent",
)

COMPANY_TERMS: tuple[str, ...] = (
    "OpenAI",
    "Anthropic",
    "Google",
    "Microsoft",
    "Meta",
    "Apple",
    "Amazon",
    "NVIDIA",
    "Hugging Face",
    "Mistral",
    "Qwen",
    "Databricks",
    "Snowflake",
    "Cloudflare",
    "GitHub",
)


class EntityExtractionService:
    def extract(self, title: str, body_text: str | None = None) -> list[ExtractedEntity]:
        text = f"{title} {body_text or ''}"
        entities: dict[tuple[str, str], ExtractedEntity] = {}

        for term in TECH_TERMS:
            if self._contains(text, term):
                canonical = canonicalize_name(term)
                entities[(canonical, "technology")] = ExtractedEntity(term, "technology", canonical)

        for term in COMPANY_TERMS:
            if self._contains(text, term):
                canonical = canonicalize_name(term)
                entities[(canonical, "company")] = ExtractedEntity(term, "company", canonical)

        return sorted(entities.values(), key=lambda item: (item.entity_type, item.name))

    @staticmethod
    def _contains(text: str, term: str) -> bool:
        pattern = rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None
