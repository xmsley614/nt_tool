from dataclasses import dataclass
import time
from typing import Optional


@dataclass
class FlightQuery:
    id: str
    origin: str
    destination: str
    date: str  # YYYY-MM-DD
    num_passengers: int
    cabin_class: str  # one of ECO, PRE, BIZ, FIRST
    max_stops: Optional[int]
    max_duration: Optional[int]  # in hours
    max_aa_points: Optional[int]
    max_ac_points: Optional[int]
    max_dl_points: Optional[int]
    exact_airport: Optional[bool]
    email: str
    last_run: int  # unix epoch time

    @staticmethod
    def from_dynamo(item):
        return FlightQuery(
            item.get("id"),
            item.get("origin"),
            item.get("destination"),
            item.get("date"),
            item.get("num_passengers"),
            item.get("cabin_class"),
            item.get("max_stops"),
            item.get("max_duration"),
            item.get("max_aa_points"),
            item.get("max_ac_points"),
            item.get("max_dl_points"),
            item.get("exact_airport"),
            item.get("email"),
            item.get("last_run")
        )


def fetch_all_queries_from_dynamo(flight_queries_table, limit=None, min_run_gap=None)\
        -> list[FlightQuery]:
    kwargs = {
        'FilterExpression': 'last_run < :last_run',
        'ExpressionAttributeValues': {
            ':last_run': int(time.time()) - min_run_gap
        }
    }

    queries = []
    resp = flight_queries_table.scan(**kwargs)
    for item in resp.get("Items"):
        queries.append(FlightQuery.from_dynamo(item))
        if len(queries) >= limit:
            return queries

    while resp.get("LastEvaluatedKey"):
        resp = flight_queries_table.scan(
            ExclusiveStartKey=resp.get("LastEvaluatedKey"),
            **kwargs
        )
        for item in resp.get("Items"):
            queries.append(FlightQuery.from_dynamo(item))
            if len(queries) >= limit:
                return queries

    return queries
