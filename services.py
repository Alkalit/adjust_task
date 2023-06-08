from abc import ABC
from collections.abc import Callable
from typing import Sequence, TypeVar
from datetime import date, datetime

from sqlalchemy import select, null, func, asc, desc, Column, Row
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db_models import CampaignStat
from models import StatOrdering, StatParams, GroupbyFields

C = TypeVar('C', bound=Callable)


class Service(Callable):

    def __call__(self, session: Session, params: BaseModel):
        ...


class BaseAnalyticsService(ABC, Service):
    ...


class AnalyticsService(BaseAnalyticsService):
    FIELDS_MAPPING: dict[str, Column] = {
        'date': CampaignStat.date,
        'channel': CampaignStat.channel,
        'country': CampaignStat.country,
        'os': CampaignStat.os,
    }

    def __call__(self, session: Session, params: StatParams) -> Sequence[Row]:
        if not params.groupby:
            expression = select(
                CampaignStat.date,
                CampaignStat.channel,
                CampaignStat.country,
                CampaignStat.os,
                CampaignStat.impressions,
                CampaignStat.clicks,
                CampaignStat.installs,
                CampaignStat.spend,
                CampaignStat.revenue,
                (CampaignStat.spend / CampaignStat.installs).label('cpi'),
            )
        else:
            columns_with_nulls: list[Column] = []
            columns: list[Column] = []
            fields: dict[GroupbyFields, int] = dict(zip(params.groupby, range(len(params.groupby))))
            for field in self.FIELDS_MAPPING:
                if field in fields:
                    column = self.FIELDS_MAPPING[field]
                    columns.append(column)
                else:
                    column = null().label(field)
                columns_with_nulls.append(column)

            expression = select(
                # null().label("date"),
                # null().label("channel"),
                # null().label("country"),
                # null().label("os"),
                *columns_with_nulls,

                func.sum(CampaignStat.impressions).label(CampaignStat.impressions.name),
                func.sum(CampaignStat.clicks).label(CampaignStat.clicks.name),
                func.sum(CampaignStat.installs).label(CampaignStat.installs.name),
                func.sum(CampaignStat.spend).label(CampaignStat.spend.name),
                func.sum(CampaignStat.revenue).label(CampaignStat.revenue.name),
                (CampaignStat.spend / CampaignStat.installs).label('cpi'),
            ).group_by(*columns)

        if params.date_from:
            date_from: date = datetime.strptime(params.date_from, '%d-%m-%Y').date()
            expression = expression.where(CampaignStat.date >= date_from)
        if params.date_to:
            date_to: date = datetime.strptime(params.date_to, '%d-%m-%Y').date()
            expression = expression.where(CampaignStat.date < date_to)
        if params.channels:
            expression = expression.where(CampaignStat.channel.in_(params.channels))
        if params.countries:
            expression = expression.where(CampaignStat.country.in_(params.countries))
        if params.os:
            expression = expression.where(CampaignStat.os.in_(params.os))
        if params.sort:
            field = self.FIELDS_MAPPING.get(params.sort)
            if params.ordering == StatOrdering.asc:
                direction = asc
            else:
                direction = desc
            expression = expression.order_by(direction(field))
        stats = session.execute(expression).all()
        return stats
