from typing import Annotated, Any, List, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if isinstance(v, ObjectId) else v)]


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    @classmethod
    def from_mongo(cls, doc):
        return cls.model_validate(doc) if doc else None

    def to_mongo(self):
        data = self.model_dump(by_alias=True)
        data.pop("_id", None)
        data.pop("id", None)
        if self.id:
            data["_id"] = ObjectId(self.id)
        return data

    def public(self):
        return self.model_dump(by_alias=False)


class Settings(BaseModel):
    wage_per_hour: float = 19.27
    cost_per_mile: float = 0.76
    markup_pct: float = 100
    floor_recurring: float = 11
    floor_one_off: float = 35
    usual_recurring: float = 14
    usual_one_off: float = 55
    market_ref_low: float = 45
    market_ref_high: float = 65
    weekdays_per_month: float = 21
    speed_sf_mph: float = 18
    speed_eastbay_mph: float = 22
    speed_cross_mph: float = 30
    bridge_minutes: float = 8
    road_factor: float = 1.3
    minutes_per_new_stop: float = 4
    auto_send_cheapest: bool = False
    demo_clock_minutes: int = 600
    real_texting: bool = False
    texting_channel: str = "sms"
    team_numbers: List[str] = []
    business_type: str = "courier"


class Business(BaseDocument):
    key: str
    name: str
    type: str
    settings: Settings


class Unit(BaseDocument):
    key: str
    business_key: str
    kind: str
    name: str
    nickname: str


class Stop(BaseDocument):
    key: str
    business_key: str
    unit_key: str
    kind: str
    customer_name: str
    window_start: float
    window_end: float
    service_minutes: float


class RoutePlan(BaseDocument):
    unit_key: str
    day_type: str
    version: int
    is_current: bool
    stops: List[Any]


class RunRecord(BaseDocument):
    stop_key: str
    unit_key: str
    date: str
    planned_arrival: float
    actual_arrival: float
    actual_service_minutes: float
    on_time: bool


class DirectoryEntry(BaseDocument):
    key: str
    name: str
    address: str
    lat: float
    lon: float


class Prospect(BaseDocument):
    key: str
    name: str
    category: str
    lat: float
    lon: float


class Request(BaseDocument):
    key: str
    number: int
    source: str
    sender: str
    raw_text: str
    status: str


class AgentThread(BaseDocument):
    business_key: str
    agent_key: str
    agent_name: str
    turns: List[Any] = []
