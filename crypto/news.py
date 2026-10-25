"""Geen ingebouwde netwerkbron; adapters moeten controleerbare items leveren."""
from datetime import timedelta
from typing import Protocol
from pydantic import AwareDatetime, Field, model_validator
from .models import Model
from .data import utc


class NewsItem(Model):
    id: str = Field(min_length=1)
    symbol: str = Field(pattern=r'^[A-Z0-9]+EUR$')
    source: str = Field(pattern=r'^https://[^\s]+$')
    title: str = Field(min_length=1)
    published: AwareDatetime
    available: AwareDatetime
    expires: AwareDatetime

    @model_validator(mode='after')
    def times(self):
        for t in (self.published,self.available,self.expires): utc(t)
        if not self.published<=self.available<self.expires: raise ValueError('Ongeldige nieuwstijden')
        return self


class NewsAdapter(Protocol):
    def fetch(self, symbol, as_of) -> list[NewsItem]: ...


class NoNews:
    def fetch(self,symbol,as_of): return []


def news_report(adapter,symbol,as_of):
    accepted,rejected=[],[]
    try: items=adapter.fetch(symbol,as_of)
    except Exception as exc: return dict(status='geen betrouwbare data',sentiment='unknown',items=[],rejections=[type(exc).__name__])
    seen=set()
    for raw in items:
        try:
            item=NewsItem.model_validate(raw)
            if item.symbol!=symbol or not item.available<=as_of<item.expires or item.id in seen:
                raise ValueError('Toekomstig, verlopen, verkeerd instrument of duplicaat')
            seen.add(item.id); accepted.append(item.model_dump(mode='json'))
        except Exception as exc: rejected.append(str(exc))
    accepted.sort(key=lambda x:(x['published'],x['id']))
    return dict(status='controleerbare bronitems' if accepted else 'geen betrouwbare data',sentiment='unknown',items=accepted,rejections=rejected,explanation='Geen automatische sentimentscore; bronbetrouwbaarheid moet door adapterbeheer worden vastgesteld')
