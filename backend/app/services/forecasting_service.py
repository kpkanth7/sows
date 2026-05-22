import logging
from datetime import timedelta

from backend.app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class ForecastingService:
    def forecast_next(self, values: list[float], horizon: int = 7) -> list[dict]:
        if not values:
            return []
        try:
            return self._forecast_with_timesfm(values, horizon)
        except Exception as exc:
            logger.info("TimesFM forecast unavailable; using naive momentum fallback: %s", exc)
            return self._naive_forecast(values, horizon)

    def _forecast_with_timesfm(self, values: list[float], horizon: int) -> list[dict]:
        import numpy as np
        import timesfm

        # TimesFM has had small API changes between releases. This adapter keeps
        # the TimesFM dependency in the forecasting path while retaining a safe
        # fallback when local model weights/configuration are not ready.
        model = timesfm.TimesFm(
            context_len=max(32, len(values)),
            horizon_len=horizon,
            input_patch_len=32,
            output_patch_len=128,
            num_layers=20,
            model_dims=1280,
            backend="cpu",
        )
        forecast, _ = model.forecast([np.array(values, dtype=float)], freq=[0])
        predictions = [float(value) for value in forecast[0][:horizon]]
        return self._format_predictions(predictions)

    def _naive_forecast(self, values: list[float], horizon: int) -> list[dict]:
        if len(values) == 1:
            predictions = [values[-1]] * horizon
        else:
            momentum = (values[-1] - values[0]) / max(len(values) - 1, 1)
            predictions = [max(values[-1] + momentum * step, 0.0) for step in range(1, horizon + 1)]
        return self._format_predictions(predictions)

    @staticmethod
    def _format_predictions(predictions: list[float]) -> list[dict]:
        today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        return [
            {
                "forecast_date": today + timedelta(days=index),
                "predicted_value": round(value, 3),
                "horizon": index,
            }
            for index, value in enumerate(predictions, start=1)
        ]
