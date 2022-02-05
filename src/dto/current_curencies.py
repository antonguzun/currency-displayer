from datetime import datetime
from typing import Sequence

from pydantic import BaseModel


class CurrentCurrencyRates(BaseModel):
    rates: Sequence[dict]
    created_at: datetime = datetime.utcnow()
