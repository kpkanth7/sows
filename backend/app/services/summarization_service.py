from backend.app.services.llm_service import LLMService, get_llm_service


class SummarizationService:
    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or get_llm_service()

    async def summarize_trends(self, trends: list[dict]) -> str:
        return await self.llm.summarize_trends(trends)

    async def explain_entity_trend(self, entity_name: str, signals: list[dict]) -> str:
        return await self.llm.explain_entity_trend(entity_name, signals)

    async def compare_entities(self, left: str, right: str, signals: list[dict]) -> str:
        return await self.llm.compare_entities(left, right, signals)
