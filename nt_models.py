import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic_computed import Computed, computed
from pydantic import BaseModel, Field, parse_obj_as
from datetime import datetime, timedelta


def convert_datetime(origin: datetime) -> str:
    origin_str = origin.isoformat()
    if 'Z' in origin_str:
        origin_str = origin_str[:-1]
    r1 = datetime.fromisoformat(origin_str)
    return r1.strftime('%Y-%m-%d %H:%M')


def convert_timedelta(td: Union[timedelta, float]) -> str:
    if type(td) == timedelta:
        seconds = td.total_seconds()
    else:
        seconds = td
    hour = int(seconds / 3600)
    minute = int(seconds / 60 % 60)
    return f'{hour}h{minute}m'


class CabinClass(str, Enum):
    Y = 'Y'
    Economy = 'Y'
    W = 'W'
    Premium = 'W'
    Premium_Economy = 'W'
    J = 'J'
    Business = 'J'
    F = 'F'
    First = 'F'


class Segment(BaseModel):
    flight_code: str
    aircraft: str
    departure: str  # TODO limit the str to only 3 chars
    excl_departure_time: datetime
    departure_time: Computed[str]

    @computed('departure_time')
    def calculate_departure_time(excl_departure_time: datetime, **kwargs):
        return convert_datetime(excl_departure_time)

    arrival: str
    excl_arrival_time: datetime
    arrival_time: Computed[str]

    @computed('arrival_time')
    def calculate_arrival_time(excl_arrival_time: datetime, **kwargs):
        return convert_datetime(excl_arrival_time)

    excl_duration_in_seconds: timedelta
    duration: Computed[str]

    @computed('duration')
    def convert_timedelta(excl_duration_in_seconds: timedelta, **kwargs):
        return convert_timedelta(excl_duration_in_seconds.total_seconds())

    excl_connection_time_in_seconds: timedelta
    connection_time: Computed[str]

    @computed('connection_time')
    def convert_connection_time(excl_connection_time_in_seconds: timedelta, **kwargs):
        return convert_timedelta(excl_connection_time_in_seconds.total_seconds())


class Pricing(BaseModel):
    cabin_class: CabinClass
    quota: int
    miles: int
    excl_cash_in_cents: float
    excl_currency: str
    cash: Computed[str]

    @computed('cash')
    def convert_cash(excl_cash_in_cents: float, excl_currency: str, **kwargs):
        return excl_currency + str(round(excl_cash_in_cents / 100, 2))

    is_mix: bool = Optional[None]
    mix_detail: str = Optional[None]

    class Config:
        use_enum_values = True


class PriceFilter(BaseModel):
    min_quota: int = 1
    preferred_classes: List[CabinClass] = [CabinClass.F, CabinClass.J, CabinClass.W, CabinClass.Y]
    max_miles_per_person: int = 9999999
    mixed_cabin_accepted: bool = True


class AirBound(BaseModel):
    segments: List[Segment]
    price: List[Pricing]

    engine: str
    excl_duration_in_all_in_seconds: timedelta
    duration_in_all: Computed[str]

    @computed('duration_in_all')
    def convert_duration_in_all(excl_duration_in_all_in_seconds: timedelta, **kwargs):
        return convert_timedelta(excl_duration_in_all_in_seconds.total_seconds())

    stops: int
    flight_codes: Computed[str]

    @computed('flight_codes')
    def calculate_aircrafts(segments: List[Segment], **kwargs):
        return '-'.join([str(x.flight_code) for x in segments])

    aircrafts: Computed[str]

    @computed('aircrafts')
    def calculate_aircrafts(segments: List[Segment], **kwargs):
        return '-'.join([str(x.aircraft) for x in segments])

    from_to: Computed[str]

    @computed('from_to')
    def calculate_from_to(segments: List[Segment], **kwargs):
        result = segments[0].departure + '-' + segments[0].arrival
        if len(segments) > 1:
            for x in range(1, len(segments)):
                if segments[x - 1].arrival == segments[x].departure:
                    result = result + '-' + segments[x].arrival
                else:
                    result = result + ',' + segments[x].departure + '-' + segments[x].arrival
        return result

    excl_departure_time: Computed[datetime] = Optional

    @computed('excl_departure_time')
    def calculate_excl_departure_time(segments: List[Segment], **kwargs):
        return segments[0].excl_departure_time

    departure_time: Computed[str]

    @computed('departure_time')
    def calculate_departure_time(excl_departure_time: datetime, **kwargs):
        return convert_datetime(excl_departure_time)

    excl_arrival_time: Computed[datetime] = Optional

    @computed('excl_arrival_time')
    def calculate_excl_arrival_time(segments: List[Segment], **kwargs):
        return segments[-1].excl_arrival_time

    arrival_time: Computed[str]

    @computed('arrival_time')
    def calculate_arrival_time(excl_arrival_time: datetime, **kwargs):
        return convert_datetime(excl_arrival_time)

    def to_cust_dict(self):
        excl_dict = {
            'excl_duration_in_all_in_seconds': True,
            'excl_departure_time': True,
            'excl_arrival_time': True,
            'price': {'__all__': {'excl_cash_in_cents', 'excl_currency'}},
            'segments': {'__all__': {'excl_departure_time',
                                     'excl_arrival_time',
                                     'excl_duration_in_seconds',
                                     'excl_connection_time_in_seconds'}}
        }
        return self.dict(exclude=excl_dict)

    def to_flatted_list(self):
        excl_dict = {
            'excl_duration_in_all_in_seconds': True,
            'excl_departure_time': True,
            'excl_arrival_time': True,
            'price': {'__all__': {'excl_cash_in_cents', 'excl_currency'}},
            'segments': False
        }
        temp = self.dict(exclude=excl_dict)
        prs = temp.pop('price')
        _ = temp.pop('segments')
        return [{**temp, **pr} for pr in prs]

    def filter_price(self, price_filter: PriceFilter):
        temp = []
        for pr in self.price:
            x = all([
                pr.quota > price_filter.min_quota,
                pr.cabin_class in price_filter.preferred_classes,
                pr.miles < price_filter.max_miles_per_person,
                True if price_filter.mixed_cabin_accepted else not pr.is_mix
                # always True if accepted, else only return not mix
            ])
            if x:
                temp.append(pr)
        self.price = temp

    class Config:
        use_enum_values = True


class YY(BaseModel):
    ex_departure_time: datetime
    departure_time: Computed[str]
    aaa: List[Pricing] = Optional

    @computed('departure_time')
    def calculate_departure_time(ex_departure_time: datetime, **kwargs):
        return convert_datetime(ex_departure_time)

    def filter_price(self):
        keep = []
        for x in self.aaa:
            if x.quota > 2:
                keep.append(x)
        self.aaa = keep


if __name__ == '__main__':
    # y = parse_obj_as(List[Pricing], [
    #     {'cabin_class': 'Y', 'quota': 9, 'miles': 20000, 'excl_cash_in_cents': '2690', 'excl_currency': 'USD'},
    #     {'cabin_class': 'J', 'quota': 1, 'miles': 30000, 'excl_cash_in_cents': '2690', 'excl_currency': 'USD'}])
    # x = YY(ex_departure_time='2023-03-26T18:00:00.000+03:00', aaa=y)
    # print(x)
    # x.filter_price()
    # print(x)

    z = PriceFilter(min_quota=2)
    print(z)
