from datetime import datetime
from parser import convert_response, results_to_excel
from searcher import Searcher

if __name__ == '__main__':
    results = []
    max_stops = 1
    origins = ['TYO', 'PVG']
    destinations = ['NYC', 'LAX']
    dates = [
        '2023-03-05',
        '2023-03-06',
        '2023-03-07',
        '2023-03-08',
        '2023-03-09',
        '2023-03-10'
    ]
    sc = Searcher()
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = sc.search_for(ori, des, date)
                v1 = convert_response(response)
                results.extend(v1)
    results_to_excel(results, max_stops=max_stops)
