from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

@dataclass
class Anomaly:
    anomaly_id: str
    record_id: Union[str, int]
    provider_id: str
    provider_name: str
    drg_definition: str
    metric: str
    value: Union[float, int]
    expected_range: tuple[Union[float, int], Union[float, int]]
    deviation: float # Percentage or absolute deviation
    confidence_score: float # A score between 0 and 1
    timestamp: datetime = datetime.now()
    description: Optional[str] = None
