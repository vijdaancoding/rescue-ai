from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_calls: int
    real_calls: int
    spam_calls: int
    dispatched: int
    false_alarms: int
    active: int
    avg_processing_latency_ms: int
    urgency_breakdown: dict[str, int]


class DayBucket(BaseModel):
    date: str
    total: int
    spam: int
    real: int


class DispatchTypeCount(BaseModel):
    dispatch_type: str
    count: int
