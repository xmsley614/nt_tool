import csv
import time
from datetime import datetime, timedelta
from multiprocessing import Pool

from aa_searcher import Aa_Searcher
from ac_searcher import Ac_Searcher
from notification import results_beautify, send_sms, send_wechat
from nt_filter import AirBoundFilter, filter_airbounds, filter_prices
from nt_models import CabinClass, PriceFilter
from nt_parser import (convert_aa_response_to_models,
                       convert_ac_response_to_models, results_to_csv,
                       results_to_excel)
from nt_sorter import get_default_sort_options, sort_airbounds
from utils import date_range


class Query(object):
    """Query struct"""

    def __init__(
            self,
            focus,
            origin,
            dest,
            start_dt,
            end_dt,
            cabin_class,  # JY
            max_duration,  # 30
            airline,  # AC/NH/EY/EK
            max_stops,  # 1
    ):
        self.focus = focus
        self.origin = origin
        self.dest = dest
        self.dates = date_range(start_dt, end_dt)
        if cabin_class:
            self.cabin_class = str2cabin(cabin_class)
        else:  # default: JY
            self.cabin_class = [CabinClass.J, CabinClass.Y]
        self.max_duration = max_duration if max_duration else 30
        # airline include: AC/NH/EY/EK
        self.airline = airline.split("/") if airline else []
        self.max_stops = max_stops if max_stops else 1


def str2cabin(cabin_class, retype=0):
    """convert string (JFYW) to cabin_class list
    ECO (Y), PRE (W), BIZ (J), FIRST (F)

    :cabin_class: string as "JY", "JFYW", etc.
    in the example, the value is read from csv file

    :returns: a cabin_class list, two formats
            format 1: [CabinClass.J, CabinClass.Y]
            format 2: ["ECO", "PRE", "BIZ", "FIRST"]

    """
    res = []
    if "J" in cabin_class:
        res.append(CabinClass.J) if retype == 0 else res.append("BIZ")
    if "Y" in cabin_class:
        res.append(CabinClass.Y) if retype == 0 else res.append("ECO")
    if "F" in cabin_class:
        res.append(CabinClass.F) if retype == 0 else res.append("FIRST")
    #  if "W" in cabin_class:
    #      res.append(CabinClass.W) if retype == 0 else res.append("PRE")
    return res


def get_queries(filename):
    """get queries from csv file"""
    queries = []
    with open(filename) as fin:
        csv_file = csv.reader(fin)
        linum = 0
        for row in csv_file:
            if linum == 0:
                linum += 1
            else:
                queries.append(row)
                linum += 1

    return queries


def worker(query):
    q = Query(
        query[0],
        query[1],
        query[2],
        query[3],
        query[4],
        query[5],
        query[6],
        query[7],
        query[8],
    )

    airbounds = []
    acs = Ac_Searcher()

    # process a query
    # class: ECO (Y), PRE (W), BIZ (J), FIRST (F) class
    # cabin_class = ["ECO", "PRE", "BIZ", "FIRST"]
    cabin_class = str2cabin(query[5], 1)

    for date in q.dates:
        print(
            f'search for {q.origin} to {q.dest} on {date} @ {datetime.now().strftime("%H:%M:%S")}'
        )
        response = acs.search_for(q.origin, q.dest, date, cabin_class)
        v1 = convert_ac_response_to_models(response)
        airbounds.extend(v1)
        # if there are high volume of network requests, add time.sleep
        # time.sleep(1)

    # apply filters
    airbound_filter = AirBoundFilter(
        max_stops=q.max_stops,
        airline_include=q.airline,
        airline_exclude=[],
    )
    price_filter = PriceFilter(
        min_quota=1,
        max_miles_per_person=999999,
        preferred_classes=q.cabin_class,
        mixed_cabin_accepted=True,
    )

    airbounds = filter_airbounds(airbounds, airbound_filter)
    airbounds = filter_prices(airbounds, price_filter)
    # TODO: add more filters
    results = []
    for x in airbounds:
        results.extend(x.to_flatted_list())

    results_to_excel(results)  # store excel with timestamps
    # results_to_csv(results) # store to history.csv

    # send notifications to phone (wechat/sms)
    msg_content = results_beautify(results)
    send_wechat(msg_content, "Remaining Quota Found!")
    #  send_sms(msg_content)

    # TODO: show/update results in browser


def search_all():
    queries = get_queries("../input/queries.csv")
    pool = Pool()
    for query in queries:
        pool.apply_async(worker, args=(query, ))
    pool.close()
    pool.join()

    print("Finish searching for all queries! Repeat searching...")
    time.sleep(5)


if __name__ == "__main__":
    while True:
        search_all()
