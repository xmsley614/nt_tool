import time
from datetime import datetime, timedelta
from nt_parser import convert_response_to_nested_jsons, results_to_excel, convert_nested_jsons_to_flatted_jsons
from searcher import Searcher


def date_range(start_date, future_date):
    date_list = []
    start_dt = start_date
    end_dt = future_date
    for n in range(int((end_dt - start_dt).days) + 1):
        d = start_dt + timedelta(n)
        date_list.append(d.strftime('%Y-%m-%d'))
    return date_list


if __name__ == '__main__':
    max_stops = 2
    origins = ['PVG','TYO', 'HKG']
    destinations = ['LAX','SFO','ORD']
    start_dt = datetime.strptime('2023-09-29', '%Y-%m-%d')
    end_dt = datetime.strptime('2023-09-29', '%Y-%m-%d')
    dates = date_range(start_dt, end_dt)
    #  means eco, pre, biz and first
    cabin_class = [
                   "RWDECO",
                   "RWDPRECC",
                   "RWDBUS",
                   "RWDFIRST",
    ]
    price_filter = {
        'quota': {
            'operator': '>=',
            'value': 1
        },
        # 'cabin_class': {
        #     'operator': 'in',
        #     'value': ['J', 'F']
        # },
        # 'is_mix': {
        #     'operator': '==',
        #     'value': False
        # }
    }
    seg_sorter = {
        'key': 'departure_time',
        'ascending': True
    }
    sc = Searcher()
    results = []
    nested_jsons_list = []
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = sc.search_for(ori, des, date, cabin_class)
                v1 = convert_response_to_nested_jsons(response)
                nested_jsons_list.extend(v1)
                # if there are high volume of network requests, add time.sleep
                # time.sleep(5)
    v2 = convert_nested_jsons_to_flatted_jsons(nested_jsons_list, seg_sorter=seg_sorter, price_filter=price_filter)
    results.extend(v2)

    results_to_excel(results, max_stops=max_stops)
