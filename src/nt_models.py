import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic_computed import Computed, computed
from pydantic import BaseModel
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
    if hour == 0:
        return f'{minute}m'
    elif hour > 0:
        return f'{hour}h{minute}m'
    else:
        return 'error duration'

class CabinClass(str, Enum):
    Y = 'Y'
    ECO = 'Y'
    Economy = 'Y'
    W = 'W'
    PRE = 'W'
    Premium = 'W'
    Premium_Economy = 'W'
    J = 'J'
    BIZ = 'J'
    Business = 'J'
    F = 'F'
    First = 'F'
    FIRST = 'F'



    @staticmethod
    def from_string(cabin_str):
        if cabin_str == "ECO":
            return CabinClass.Economy
        elif cabin_str == "PRE":
            return CabinClass.Premium
        elif cabin_str == "BIZ":
            return CabinClass.Business
        elif cabin_str == "FIRST":
            return CabinClass.First
        raise Exception(f"Unknown cabin string: {cabin_str}")

    def __gt__(self, other):
        if self == 'F' and other != 'F':
            return True
        elif self == 'J' and other != 'F' and other != 'J':
            return True
        elif self == 'W' and other != 'F' and other != 'J' and other != 'W':
            return True
        else:
            return False

    def __lt__(self, other):
        return other.__gt__(self)

    def __ge__(self, other):
        if self == 'F':
            return True
        elif self == 'J' and other != 'F':
            return True
        elif self == 'W' and other != 'F' and other != 'J':
            return True
        elif self == 'Y' and other != 'F' and other != 'J' and other != 'W':
            return True
        else:
            return False

    def __le__(self, other):
        return other.__ge__(self)


class Segment(BaseModel):
    flight_code: str
    aircraft: str
    departure: str  # TODO limit the str to only 3 chars
    excl_departure_time: datetime
    excl_cabin_exist: Optional[List[CabinClass]]
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
    excl_miles: int
    miles: Computed[str]

    @computed('miles')
    def convert_cash(excl_miles: int, **kwargs):
        return str(round(excl_miles / 1000, 1)) + 'k'

    excl_cash_in_base_unit: float
    excl_currency: str
    cash: Computed[str]

    @computed('cash')
    def convert_cash(excl_cash_in_base_unit: float, excl_currency: str, **kwargs):
        return excl_currency + str(round(excl_cash_in_base_unit, 2))

    is_mix: bool = Optional[bool]
    mix_detail: str = Optional[str]

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
                connection = segments[x].excl_departure_time - segments[x - 1].excl_arrival_time
                connection_str = convert_timedelta(connection)
                if segments[x - 1].arrival == segments[x].departure:
                    result = result + f'({connection_str})' + '-' + segments[x].arrival
                else:
                    result = result + f'({connection_str})' + ',' + segments[x].departure + '-' + segments[x].arrival
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
            'price': {'__all__': {'excl_cash_in_base_unit', 'excl_currency'}},
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
            'price': {'__all__': {'excl_cash_in_base_unit', 'excl_currency', 'excl_miles'}},
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
                pr.quota >= price_filter.min_quota,
                pr.cabin_class in price_filter.preferred_classes,
                pr.excl_miles <= price_filter.max_miles_per_person,
                True if price_filter.mixed_cabin_accepted else not pr.is_mix
                # always True if accepted, else only return not mix
            ])
            if x:
                temp.append(pr)
        self.price = temp

    class Config:
        use_enum_values = True

