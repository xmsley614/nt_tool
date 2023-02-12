import time
from datetime import datetime, timedelta
from nt_parser import convert_response, results_to_excel
from searcher import Searcher


def date_range(start_date,future_date):
    date_list = []
    start_dt = start_date
    end_dt = future_date
    for n in range(int((end_dt - start_dt).days)+1):
        d = start_dt + timedelta(n)
        date_list.append(d.strftime('%Y-%m-%d'))
    return date_list



if __name__ == '__main__':
    results = []
    max_stops = 1
    origins = ['BOS','ORD']
    destinations = ['FRA']
    start_dt=datetime.strptime('2023-05-10', '%Y-%m-%d')
    end_dt = datetime.strptime('2023-05-15', '%Y-%m-%d')
    dates=date_range(start_dt,end_dt)

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
