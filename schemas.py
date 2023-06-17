from typing import NewType
from datetime import date
from decimal import Decimal
from pydantic import BaseModel

CampaignStatId = NewType('CampaignStatId', int)
Channel = NewType('Channel', str)
Country = NewType('Country', str)
OS = NewType('OS', str)
Money = NewType('Money', Decimal)


class CampaignStatSchema(BaseModel):
    date: date | None
    channel: Channel | None
    country: Country | None
    os: OS | None
    impressions: int
    clicks: int
    installs: int
    spend: Money
    revenue: Money
    cpi: Money
