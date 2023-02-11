from datetime import datetime

import pandas as pd
from styleframe import StyleFrame, Styler

from parser import convert_response
from searcher import Searcher


def results_to_excel(results, max_stops: int = 1):
    df = pd.DataFrame(results)
    df.sort_values('stops', ascending=True, inplace=True)
    df = df[df['stops'] <= max_stops]
    df.reset_index()
    sf = StyleFrame(df, styler_obj=Styler(wrap_text=True))
    sf.set_column_width(['departure_time', 'arrival_time'], width=20)
    sf.set_column_width(['from_to', 'cash'], width=15)
    sf.to_excel('output.xlsx').save()


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
