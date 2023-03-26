from typing import List, Dict
from nt_models import AirBound
from pydantic import BaseModel


class SortOption(BaseModel):
    priority: int  # smaller number means higher priority
    ascending: bool = True
    key: str  # exactly match the field name in Airbound class


def get_default_sort_options(discription: str) -> List[SortOption]:
    if discription == 'Least stops':
        return [SortOption(priority=1, key='stops', ascending=True)]
    elif discription == 'Shortest trip':
        return [SortOption(priority=1, key='excl_duration_in_all_in_seconds', ascending=True)]
    elif discription == 'Earliest departure time':
        return [SortOption(priority=1, key='excl_departure_time', ascending=True)]
    elif discription == 'Earliest arrival time':
        return [SortOption(priority=1, key='excl_arrival_time', ascending=True)]
    else:
        return [SortOption(priority=1, key='stops', ascending=True)]


def sort_airbounds(origins: List[AirBound], sort_options: List[SortOption] = None):
    if sort_options is None:
        sort_options = [SortOption(priority=1, ascending=True, key='stops')]
    sort_options.sort(key=lambda x: x.priority, reverse=True)
    # print(sort_options)
    for so in sort_options:
        origins.sort(key=lambda x: x.__getattribute__(so.key), reverse=not so.ascending)
    return origins
