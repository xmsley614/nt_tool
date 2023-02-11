import time
from datetime import datetime
from parser import convert_response, results_to_excel
from searcher import Searcher

if __name__ == '__main__':
    results = []
    max_stops = 1
    origins = ['BOS', 'ORD']
    destinations = ['FRA']
    dates = [
        '2023-02-11',
        # '2023-02-12',
        # '2023-02-13',
        # '2023-02-14',
    ]
    sc = Searcher()
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = sc.search_for(ori, des, date)
                v1 = convert_response(response)
                results.extend(v1)
                # 搜索量大返回异常时，加上延迟
                # time.sleep(5)
    results_to_excel(results, max_stops=max_stops)
