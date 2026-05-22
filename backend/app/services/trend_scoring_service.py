import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TrendScore:
    mention_count: int
    score_sum: float
    item_count: int
    trend_score: float


class TrendScoringService:
    def score(self, mention_count: int, score_sum: float, item_count: int) -> TrendScore:
        signal = mention_count * 2.0
        engagement = math.log1p(max(score_sum, 0.0)) * 1.5
        breadth = math.sqrt(max(item_count, 1))
        trend_score = round(signal + engagement + breadth, 3)
        return TrendScore(
            mention_count=mention_count,
            score_sum=round(score_sum, 3),
            item_count=item_count,
            trend_score=trend_score,
        )
