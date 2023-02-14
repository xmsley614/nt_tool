from datetime import datetime

import pandas as pd
import requests
from styleframe import StyleFrame, Styler

from nt_filter import filter_price
from nt_sorter import sort_segs


def convert_miles(miles: int) -> str:
    return str(miles / 1000) + 'k'


def convert_duration(seconds: int) -> str:
    hour = int(seconds / 3600)
    min = int(seconds / 60 % 60)
    return f'{hour}h{min}m'


def convert_datetime(origin_str: str) -> str:
    if 'Z' in origin_str:
        origin_str = origin_str[:-1]
    r1 = datetime.fromisoformat(origin_str)
    return r1.strftime('%Y-%m-%d %H:%M')


def convert_cash(cash: int) -> str:
    return 'CAD' + str(cash / 100)


def convert_mix(availabilityDetails) -> str:
    cabin_dict = {
        'business': 'J',
        'eco': 'Y',
        'ecoPremium': 'PY',
        'first': 'F'
    }
    return "+".join([str(x['mileagePercentage']) + '%' + cabin_dict[x['cabin']] for x in availabilityDetails])


def convert_response_to_nested_jsons(response: requests.Response) -> list:
    """
    Convert response from searcher request.
    :param response: Response of searcher request.
    :return: List of nested json. Each json means an itinerary.
    """
    if response.status_code != 200:
        return list()
    else:
        response_json = response.json()
        air_bounds = response_json.get('data', {}).get('airBoundGroups', []) if response_json is not None else {}
        flights_info_dict = response_json.get('dictionaries', {}).get('flight',
                                                                      {}) if response_json is not None else {}
        results = []
        cabin_class_dict = {
            'STANDARD': 'Y',
            # 'PYLOW': 'PY',  # 目前发现所有超经舱位均为AC自己的动态，且子舱位会使用O舱，与星盟伙伴头等奖励客票F舱子舱位O有冲突，暂时去除所有PY结果。
            'EXECLOW': 'J',
            'FIRSTLOW': 'F',
        }
        saver_class_list = ['X', 'I', 'O']
        for r in air_bounds:
            r = dict(r)
            prices_raw = [rr for rr in r['airBounds']]
            segs_raw = [rr for rr in r['boundDetails']['segments']]
            prices = []
            for pr in prices_raw:
                if pr['fareFamilyCode'] in cabin_class_dict.keys() and \
                        all([x['bookingClass'] in saver_class_list for x in pr['availabilityDetails']]):
                    temp = {
                        'cabin_class': cabin_class_dict[pr['fareFamilyCode']],
                        'quota': min([x['quota'] for x in pr['availabilityDetails']]),
                        'miles': pr['airOffer']['milesConversion']['convertedMiles']['base'],
                        'cash': pr['airOffer']['milesConversion']['convertedMiles']['totalTaxes'],
                        'is_mix': pr.get('isMixedCabin', False),
                        'mix_detail': convert_mix(pr['availabilityDetails']) if pr.get('isMixedCabin', False) else ""
                    }
                    prices.append(temp)
                else:
                    continue
            segs = []
            for sg in segs_raw:
                flight_info = flights_info_dict[sg['flightId']]
                temp = {
                    'connection_time': sg.get('connectionTime', 0),
                    'flight_code': flight_info['marketingAirlineCode'] + flight_info['marketingFlightNumber'],
                    'aircraft': flight_info['aircraftCode'],
                    'departure': flight_info['departure']['locationCode'],
                    'departure_time': flight_info['departure']['dateTime'],
                    'arrival': flight_info['arrival']['locationCode'],
                    'arrival_time': flight_info['arrival']['dateTime'],
                    'duration': flight_info['duration']
                }
                segs.append(temp)

            v = {
                'duration_in_all': r['boundDetails']['duration'],
                'stops': len(segs_raw) - 1,
                'segments': segs,
                'price': prices
            }
            results.append(v)
        return results


def convert_nested_jsons_to_flatted_jsons(origin_results: list,
                                          seg_sorter: dict = None,
                                          price_filter: dict = {}) -> list:
    # print(origin_results)
    sorted_results = sort_segs(origin_results, seg_sorter)
    # sorted_results = origin_results

    flatted_results = []
    for result in sorted_results:
        segs = result['segments']
        segs_single = {
            'flight_code': '\n'.join([x['flight_code'] for x in segs]),
            'aircraft': '\n'.join([str(x['aircraft']) for x in segs]),
            'from_to': '\n'.join([x['departure'] + '-' + x['arrival'] for x in segs]),
            'departure_time': '\n'.join([convert_datetime(x['departure_time']) for x in segs]),
            'arrival_time': '\n'.join([convert_datetime(x['arrival_time']) for x in segs]),
            'duration': '\n'.join([convert_duration(x['duration']) for x in segs]),
            'connection_time': '\n'.join([convert_duration(x['connection_time']) for x in segs]),
        }
        prices = result['price']
        prices_filtered = filter_price(prices, price_filter)
        #  如果所有票价均已被过滤，那么直接进入下一组循环。
        if len(prices_filtered) == 0:
            continue
        prices_single = {
            'cabin_class_and_quota': '\n'.join([x['cabin_class'] + str(x['quota']) for x in prices_filtered]),
            'miles': '\n'.join([convert_miles(x['miles']) for x in prices_filtered]),
            'cash': '\n'.join([convert_cash(x['cash']) for x in prices_filtered]),
            'is_mix': '\n'.join([str(x['is_mix']) for x in prices_filtered]),
            'mix_detail': '\n'.join([x['mix_detail'] for x in prices_filtered]),
        }
        v1 = {
            'stops': result['stops'],
            'duration_in_all': convert_duration(result['duration_in_all']),
        }
        flatted_results.append({**v1, **segs_single, **prices_single})
    return flatted_results


def results_to_excel(results, max_stops: int = 1):
    if len(results) == 0:
        print('No results at all, finished.')
    else:
        df = pd.DataFrame(results)
        df.reset_index()
        sf = StyleFrame(df, styler_obj=Styler(wrap_text=True))
        sf.set_column_width(['departure_time', 'arrival_time', 'mix_detail'], width=20)
        sf.set_column_width(['from_to', 'cash', ], width=15)
        sf.to_excel('output.xlsx').save()
        print('Success! Please check the output excel file.')


def results_to_dash_table(results):
    df = pd.DataFrame(results)
    return df.to_dict('records')
