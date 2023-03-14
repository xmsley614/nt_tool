import time
from datetime import datetime, timedelta

from aa_searcher import Aa_Searcher
from nt_models import PriceFilter, CabinClass
from nt_parser import results_to_excel, convert_nested_jsons_to_flatted_jsons, \
    convert_aa_response_to_models, filter_models
from utils import date_range

if __name__ == '__main__':
    max_stops = 1
    origins = ['PEK']
    destinations = ['SYD', 'MEL', 'BNE']
    start_dt = '2023-04-15'
    end_dt = '2023-04-30'
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
        max_miles_per_person=999999,
        preferred_classes=[CabinClass.J, CabinClass.F, CabinClass.Y],
        mixed_cabin_accepted=True
    )
    seg_sorter = {
        'key': 'departure_time',  # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
        'ascending': True
    }
    aas = Aa_Searcher()
    airbounds = []
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = aas.search_for(ori, des, date, cabin_class)
                v1 = convert_aa_response_to_models(response)
                airbounds.extend(v1)
                # if there are high volume of network requests, add time.sleep
                # time.sleep(1)

    airbounds = filter_models(airbounds, price_filter)
    results = []
    for x in airbounds:
        results.extend(x.to_flatted_list())
    results_to_excel(results, max_stops=max_stops)
