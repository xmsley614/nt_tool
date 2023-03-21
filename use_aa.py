import time
from datetime import datetime, timedelta

from aa_searcher import Aa_Searcher
from nt_models import PriceFilter, CabinClass, AirBoundFilter
from nt_parser import results_to_excel, convert_aa_response_to_models
from nt_filter import filter_prices, filter_airbounds
from utils import date_range

if __name__ == '__main__':
    origins = ['DOH']
    destinations = ['TYO']
    start_dt = '2023-05-05'
    end_dt = '2023-05-25'
    dates = date_range(start_dt, end_dt)
    #  means eco, pre, biz and first
    cabin_class = [
        "ECO",
        "PRE",
        "BIZ",
        "FIRST"
    ]
    airbound_filter = AirBoundFilter(
        max_stops=1,
        airline_include=[],
        airline_exclude=[],
    )
    price_filter = PriceFilter(
        min_quota=1,
        max_miles_per_person=999999,
        preferred_classes=[CabinClass.J, CabinClass.F, CabinClass.Y],
        mixed_cabin_accepted=True
    )
    # seg_sorter = {
    #     'key': 'departure_time',  # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
    #     'ascending': True
    # }
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
    airbounds = filter_airbounds(airbounds, airbound_filter)
    airbounds = filter_prices(airbounds, price_filter)
    results = []
    for x in airbounds:
        results.extend(x.to_flatted_list())
    results_to_excel(results)
