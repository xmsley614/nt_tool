import time
from datetime import datetime, timedelta
from nt_models import CabinClass, PriceFilter
from nt_parser import results_to_excel, convert_ac_response_to_models2
from nt_filter import filter_prices, filter_airbounds, AirBoundFilter
from ac_searcher2 import Ac_Searcher2
from utils import date_range

if __name__ == '__main__':
    origins = ['TYO']
    destinations = ['LAX']
    start_dt = '2023-06-07'
    end_dt = '2023-06-07'
    dates = date_range(start_dt, end_dt)
    number_of_passengers = 1
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
    acs = Ac_Searcher2()
    airbounds = []
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = acs.search_for(ori, des, date, number_of_passengers)
                print(response.status_code)
                v1 = convert_ac_response_to_models2(response)
                airbounds.extend(v1)
                # if there are high volume of network requests, add time.sleep
                # time.sleep(1)
    airbounds = filter_airbounds(airbounds, airbound_filter)
    airbounds = filter_prices(airbounds, price_filter)
    results = []
    for x in airbounds:
        results.extend(x.to_flatted_list())
    results_to_excel(results)
