from typing import TypedDict

from backend.app.services.summarization_service import SummarizationService


class SummarizationState(TypedDict):
    trends: list[dict]
    summary: str


def build_summarization_graph():
    from langgraph.graph import END, StateGraph

    async def summarize(state: SummarizationState) -> SummarizationState:
        summary = await SummarizationService().summarize_trends(state["trends"])
        return {"trends": state["trends"], "summary": summary}

    workflow = StateGraph(SummarizationState)
    workflow.add_node("summarize", summarize)
    workflow.set_entry_point("summarize")
    workflow.add_edge("summarize", END)
    return workflow.compile()
