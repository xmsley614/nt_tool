import time
from datetime import datetime, timedelta
from nt_parser import convert_response, results_to_excel
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
    results = []
    max_stops = 2
    origins = ['PVG','TYO', 'HKG']
    destinations = ['LAX','SFO','ORD']
    start_dt = datetime.strptime('2023-09-27', '%Y-%m-%d')
    end_dt = datetime.strptime('2023-09-29', '%Y-%m-%d')
    dates = date_range(start_dt, end_dt)
    # 分别对应经济、超经、商务、头等，如果不想要某个舱位的结果，可以在列表中去除。
    cabin_class = [
                   "RWDECO",
                   "RWDPRECC",
                   "RWDBUS",
                   "RWDFIRST",
    ]

    price_filter = {
        # 'quota': {
        #     'operator': '>=',
        #     'value': 1
        # },
        # 'cabin_class': {
        #     'operator': 'in',
        #     'value': ['J', 'F']
        # },
        # 'is_mix': {
        #     'operator': '==',
        #     'value': False
        # }
    }
    sc = Searcher()
    for ori in origins:
        for des in destinations:
            for date in dates:
                print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
                response = sc.search_for(ori, des, date, cabin_class)
                v1 = convert_response(response, price_filter=price_filter)
                results.extend(v1)
                # 搜索量大返回异常时，加上延迟
                # time.sleep(5)
    results_to_excel(results, max_stops=max_stops)
