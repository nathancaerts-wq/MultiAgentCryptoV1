import json
from urllib.request import urlopen
from decimal import Decimal
from .models import MarketRules


class BinancePublic:
    """Alleen publieke GET endpoints; geen credentials en geen ordermethoden."""
    BASE = 'https://api.binance.com'

    def exchange_info(self):
        with urlopen(self.BASE + '/api/v3/exchangeInfo', timeout=15) as response:
            return json.load(response)

    @staticmethod
    def rules(document):
        result = []
        for symbol in document['symbols']:
            if symbol['quoteAsset'] != 'EUR' or symbol['status'] != 'TRADING' or not symbol.get('isSpotTradingAllowed', False):
                continue
            filters = {f['filterType']: f for f in symbol['filters']}
            if not {'LOT_SIZE', 'PRICE_FILTER'} <= filters.keys():
                continue
            n = filters.get('NOTIONAL', filters.get('MIN_NOTIONAL'))
            if n is None:
                continue
            lot, price = filters['LOT_SIZE'], filters['PRICE_FILTER']
            result.append(MarketRules(symbol=symbol['symbol'], enabled=True, min_qty=lot['minQty'], max_qty=lot['maxQty'], step=lot['stepSize'], tick=price['tickSize'], min_notional=n['minNotional'], max_notional=n.get('maxNotional')))
        return result


def select_universe(rules, metrics, min_volume=100000, min_depth=1000, max_spread=.003, min_history=1000):
    selected = []
    for rule in rules:
        m = metrics.get(rule.symbol)
        if m and m.get('quality') is True and m.get('volume', 0) >= min_volume and m.get('depth', 0) >= min_depth and 0 <= m.get('spread', -1) <= max_spread and m.get('history', 0) >= min_history:
            selected.append(rule.symbol)
    return selected
