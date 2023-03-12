import time
from datetime import datetime, timedelta

from nt_models import PriceFilter, CabinClass
from nt_parser import convert_ac_response_to_models, results_to_excel, convert_nested_jsons_to_flatted_jsons, \
    filter_models
from ac_searcher import Ac_Searcher
from utils import date_range

if __name__ == '__main__':
    max_stops = 1
    origins = ['NYC', 'ORD', 'IAD', 'YYZ']
    destinations = ['AUH']
    start_dt = '2023-10-05'
    end_dt = '2023-10-07'
    dates = date_range(start_dt, end_dt)
    #  means eco, pre, biz and first
    cabin_class = [
        "ECO",
        "PRE",
        "BIZ",
        "FIRST"
    ]
    price_filter = PriceFilter(
        min_quota=2,
        max_miles_per_person=75000,
        preferred_classes=[CabinClass.J, CabinClass.F, CabinClass.Y],
        mixed_cabin_accepted=True
    )
    seg_sorter = {
        'key': 'departure_time',  # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
        'ascending': True
    }
    acs = Ac_Searcher()
    airbounds = []
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = acs.search_for(ori, des, date, cabin_class)
                v1 = convert_ac_response_to_models(response)
                airbounds.extend(v1)
                # if there are high volume of network requests, add time.sleep
                # time.sleep(1)

    airbounds = filter_models(airbounds, price_filter)
    results = []
    for x in airbounds:
        results.extend(x.to_flatted_list())
    results_to_excel(results, max_stops=max_stops)
