"""Rekenprimitieven voor de preregistreerde marktindex; geen orderroute."""
from decimal import Decimal as D
from .sim_execution import FillCosts, rounded


def cash_benchmark():
 return dict(cash=D(200),equity=D(200),fees=D(0),exposure=D(0))


class BuyHoldIndex:
 def __init__(self,coins,costs=None):
  if len(set(coins))!=6: raise ValueError('Zes vaste munten vereist')
  self.coins=tuple(sorted(coins));self.costs=costs or FillCosts()
  self.cash=D(200);self.positions={};self.fees=D(0);self.started=False
 def enter(self,opens,eligible):
  if self.started: raise ValueError('Eenmalige indexinstap')
  if set(opens)!=set(self.coins) or set(eligible)!=set(self.coins): raise ValueError('Volledig universum vereist')
  if any(not p.is_finite() or p<=0 for p in opens.values()): raise ValueError('Ongeldige prijs')
  self.started=True
  budget=D(200)/6; step=D('.000000000001')
  for s in self.coins:
   if not eligible[s]: continue
   p=opens[s]*(1+self.costs.spread/2+self.costs.slippage)
   q=rounded(budget/(p*(1+self.costs.fee)),step)
   while q*p+self.costs.charge(q,p)>budget: q-=step
   fee=self.costs.charge(q,p)
   self.cash-=q*p+fee;self.fees+=fee;self.positions[s]=q
 def value(self,closes):
  if any(s not in closes or not closes[s].is_finite() or closes[s]<=0 for s in self.positions):
   raise ValueError('Ontbrekende/ongeldige aangehouden indexkoers')
  equity=self.cash
  for s,q in self.positions.items():
   p=closes[s]*(1-self.costs.spread/2-self.costs.slippage)
   equity+=q*p-self.costs.charge(q,p)
  return equity


def benchmark_calendar(stage):
 """Alleen preregistreerde D/V-kalender, geen testvrijgave of rendement."""
 from .readiness import PERIODS,dt
 if stage not in ('development','validation'): raise ValueError('Gesloten of onbekende benchmarkperiode')
 start,end=PERIODS[stage]
 return dict(start=start,end=end,index_entry=dt('2024-01-08') if stage=='development' else start,
             latest_entry=end-__import__('datetime').timedelta(hours=4,minutes=15))
