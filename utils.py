import datetime
from datetime import timedelta
from typing import List
from datetime import datetime


def date_range(start_date:str, end_date:str) ->List[str]:
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    date_list = []
    for n in range(int((end_dt - start_dt).days) + 1):
        d = start_dt + timedelta(n)
        date_list.append(d.strftime('%Y-%m-%d'))
    return date_list
