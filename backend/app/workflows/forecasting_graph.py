from typing import TypedDict

from backend.app.services.forecasting_service import ForecastingService


class ForecastingState(TypedDict):
    values: list[float]
    horizon: int
    predictions: list[dict]


def build_forecasting_graph():
    from langgraph.graph import END, StateGraph

    def forecast(state: ForecastingState) -> ForecastingState:
        predictions = ForecastingService().forecast_next(state["values"], state["horizon"])
        return {**state, "predictions": predictions}

    workflow = StateGraph(ForecastingState)
    workflow.add_node("forecast", forecast)
    workflow.set_entry_point("forecast")
    workflow.add_edge("forecast", END)
    return workflow.compile()
