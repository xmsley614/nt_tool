from typing import List

from pydantic import BaseModel

from nt_models import AirBound, PriceFilter


class AirBoundFilter(BaseModel):
    max_stops: int = -1
    airline_include: List[str] = []
    airline_exclude: List[str] = []


def filter_airbounds(airbounds: List[AirBound], airbound_filter: AirBoundFilter) -> List[AirBound]:
    result = []
    for ab in airbounds:
        bool_list = []
        if airbound_filter.max_stops == -1:
            bool_list.append(True)
        else:
            bool_list.append(ab.stops <= airbound_filter.max_stops)
        if len(airbound_filter.airline_include) == 0:
            bool_list.append(True)
        else:
            bool_list.append(any([x.upper() in ab.flight_codes for x in airbound_filter.airline_include]))
        if len(airbound_filter.airline_exclude) == 0:
            bool_list.append(True)
        else:
            bool_list.append(not any([x.upper() in ab.flight_codes for x in airbound_filter.airline_exclude]))
        if all(bool_list):
            result.append(ab)
    return result


def filter_prices(airbounds: List[AirBound], price_filter: PriceFilter) -> List[AirBound]:
    result = []
    for ab in airbounds:
        ab.filter_price(price_filter)
        if len(ab.price) > 0:
            result.append(ab)
    return result
