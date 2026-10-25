from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator


def now():
    return datetime.now(timezone.utc)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Message(Model):
    agent_id: str = Field(min_length=1)
    event_id: UUID = Field(default_factory=uuid4)
    coin: str = Field(min_length=1)
    timestamp: AwareDatetime = Field(default_factory=now)
    timeframe: str = Field(min_length=1)
    data: dict[str, Any] = Field(min_length=1)
    result: dict[str, Any] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    ttl_seconds: int = Field(gt=0, le=86400)
    status: Literal["ok", "error"] = "ok"
    errors: tuple[str, ...] = ()

    @model_validator(mode="after")
    def coherent(self):
        if (self.status == "error") != bool(self.errors):
            raise ValueError("Status en fouten komen niet overeen")
        if self.timestamp.utcoffset().total_seconds() != 0:
            raise ValueError("UTC vereist")
        return self

    def usable(self):
        age = (now() - self.timestamp).total_seconds()
        return self.status == "ok" and 0 <= age < self.ttl_seconds


class Proposal(Model):
    event_id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    stop: Decimal = Field(gt=0)
    timestamp: AwareDatetime = Field(default_factory=now)

    @model_validator(mode="after")
    def stop_below_entry(self):
        if self.stop >= self.price:
            raise ValueError("Long spot stop moet lager zijn dan instapprijs")
        return self


class Limits(Model):
    trade_risk: Decimal = Field(default=Decimal('.01'), gt=0, le=1)
    exposure: Decimal = Field(default=Decimal('.5'), gt=0, le=1)
    daily_loss: Decimal = Field(default=Decimal('.03'), gt=0, le=1)
    drawdown: Decimal = Field(default=Decimal('.1'), gt=0, le=1)
    correlation: Decimal = Field(default=Decimal('.8'), gt=0, le=1)
    max_age: int = Field(default=60, gt=0)


class MarketRules(Model):
    symbol: str
    quote: Literal['EUR'] = 'EUR'
    enabled: bool
    min_qty: Decimal = Field(ge=0)
    max_qty: Decimal = Field(gt=0)
    step: Decimal = Field(gt=0)
    tick: Decimal = Field(gt=0)
    min_notional: Decimal = Field(ge=0)
    max_notional: Decimal | None = Field(default=None, gt=0)
    timestamp: AwareDatetime = Field(default_factory=now)
