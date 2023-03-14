from datetime import datetime
from typing import List

import pandas as pd
import requests
from styleframe import StyleFrame, Styler

from nt_filter import filter_price
from nt_models import Pricing, Segment, AirBound, PriceFilter
from nt_sorter import sort_segs


def convert_miles(miles: int) -> str:
    return str(miles / 1000) + 'k'


def convert_aa_quota(origin_quota: int) -> int:
    """
    For AA, seatsRemaining usually shows 0 if there are many seats.
    So 0 should be turned to 9.
    For the situation there is really no seat, then other fields like 'extendedFareCode' will also be empty.
    We can take care of it outside this function.
    """
    if origin_quota == 0:
        return 9
    else:
        return origin_quota


def convert_duration(seconds: int) -> str:
    hour = int(seconds / 3600)
    min = int(seconds / 60 % 60)
    return f'{hour}h{min}m'


def convert_datetime(origin_str: str) -> str:
    if 'Z' in origin_str:
        origin_str = origin_str[:-1]
    r1 = datetime.fromisoformat(origin_str)
    return r1.strftime('%Y-%m-%d %H:%M')


def convert_cash(cash: int, currency) -> str:
    return currency + str(cash / 100)


def convert_mix(availabilityDetails) -> str:
    cabin_dict = {
        'business': 'J',
        'eco': 'Y',
        'ecoPremium': 'PY',
        'first': 'F'
    }
    return "+".join([str(x['mileagePercentage']) + '%' + cabin_dict[x['cabin']] for x in availabilityDetails])


def convert_ac_response_to_models(response: requests.Response) -> List:
    """
    Convert response from searcher request.
    param response: Response of searcher request.
    :return: List of nested json. Each json means an itinerary.
    """
    if response.status_code != 200:
        return list()
    else:
        response_json = response.json()
        air_bounds_json = response_json.get('data', {}).get('airBoundGroups', []) if response_json is not None else {}
        flights_info_dict = response_json.get('dictionaries', {}).get('flight',
                                                                      {}) if response_json is not None else {}
        results = []
        cabin_class_dict = {
            'STANDARD': 'Y',
            # 'PYLOW': 'W',  # 目前发现所有超经舱位均为AC自己的动态，且子舱位会使用O舱，与星盟伙伴头等奖励客票F舱子舱位O有冲突，暂时去除所有PY结果。
            'EXECLOW': 'J',
            'FIRSTLOW': 'F',
        }
        saver_class_list = ['X', 'I', 'A']
        for r in air_bounds_json:
            r = dict(r)
            prices_raw = [rr for rr in r['airBounds']]
            segs_raw = [rr for rr in r['boundDetails']['segments']]
            prices = []
            for pr in prices_raw:
                #  keep price with conditions below:
                #  fareFamilyCode in cabin_class_dict.keys means the lowest fare of each physical class
                #  then keep all flights without AC code,
                #  or with AC code which booking class is XIO.
                if pr['fareFamilyCode'] in cabin_class_dict.keys():
                    if all(['AC' not in str(x['flightId']).split('-')[1] or
                            (x['bookingClass'] in saver_class_list and 'AC' in str(x['flightId']).split('-')[1])
                            for x in pr['availabilityDetails']]):
                        temp_pricing = Pricing(
                            cabin_class=cabin_class_dict[pr['fareFamilyCode']],
                            quota=min([x['quota'] for x in pr['availabilityDetails']]),
                            miles=pr['airOffer']['milesConversion']['convertedMiles']['base'],
                            excl_cash_in_cents=pr['airOffer']['milesConversion']['convertedMiles']['totalTaxes'],
                            excl_currency='CAD',
                            is_mix=pr.get('isMixedCabin', False),
                            mix_detail=convert_mix(pr['availabilityDetails']) if pr.get('isMixedCabin', False) else "N/A"
                        )
                        prices.append(temp_pricing)
                else:
                    continue
            segs = []
            for sg in segs_raw:
                flight_info = flights_info_dict[sg['flightId']]
                temp_seg = Segment(
                    flight_code=flight_info['marketingAirlineCode'] + flight_info['marketingFlightNumber'],
                    aircraft=flight_info['aircraftCode'],
                    departure=flight_info['departure']['locationCode'],  # TODO limit the str to only 3 chars
                    excl_departure_time=flight_info['departure']['dateTime'],
                    arrival=flight_info['arrival']['locationCode'],
                    excl_arrival_time=flight_info['arrival']['dateTime'],
                    # excl_duration_in_seconds=sg['legs'][0]['durationInMinutes'] * 60,
                    excl_duration_in_seconds=flight_info['duration'],
                    # excl_connection_time_in_seconds=sg['legs'][0]['connectionTimeInMinutes'] * 60,
                    excl_connection_time_in_seconds=sg.get('connectionTime', 0),
                )
                segs.append(temp_seg)
            air_bound = AirBound(
                engine='AC',
                excl_duration_in_all_in_seconds=r['boundDetails']['duration'],
                stops=len(segs_raw) - 1,
                segments=segs,
                price=prices
            )
            results.append(air_bound)
        return results


def filter_models(airbounds: List[AirBound], price_filter: PriceFilter) -> List[AirBound]:
    result = []
    for ab in airbounds:
        ab.filter_price(price_filter)
        if len(ab.price) > 0:
            result.append(ab)
    return result


def convert_aa_response_to_models(response: requests.Response) -> List:
    if response.status_code != 200:
        return []
    else:
        response_json = response.json()
        air_bounds_json = response_json.get('slices', []) if response_json is not None else {}
    results = []
    cabin_class_dict = {
        'COACH': 'Y',
        'PREMIUM_ECONOMY': 'W',
        'BUSINESS': 'J',
        'FIRST': 'F',
    }
    # saver_class_list = ['X', 'I', 'O']
    for r in air_bounds_json:
        r = dict(r)
        prices_raw = [rr['cheapestPrice'] for rr in r['productPricing']]
        prices = []
        for pr in prices_raw:
            if pr['extendedFareCode'] != '':
                temp_pricing = Pricing(
                    cabin_class=cabin_class_dict[pr['productType']],
                    quota=convert_aa_quota(pr['seatsRemaining']) if pr['extendedFareCode'] != '' else 0,
                    miles=pr['perPassengerAwardPoints'],
                    excl_cash_in_cents=pr['perPassengerTaxesAndFees']['amount'] * 100,
                    excl_currency=pr['perPassengerTaxesAndFees']['currency'],
                    is_mix=False,
                    mix_detail='N/A'  # TODO add mix info
                )
                prices.append(temp_pricing)
            else:
                continue
        segs_raw = [rr for rr in r['segments']]
        segs = []
        for sg in segs_raw:
            temp_seg = Segment(
                flight_code=sg['flight']['carrierCode'] + sg['flight']['flightNumber'],
                aircraft=sg['legs'][0]['aircraft']['code'],
                departure=sg['origin']['code'],  # TODO limit the str to only 3 chars
                excl_departure_time=sg['departureDateTime'],
                arrival=sg['destination']['code'],
                excl_arrival_time=sg['arrivalDateTime'],
                # excl_duration_in_seconds=sg['legs'][0]['durationInMinutes'] * 60,
                excl_duration_in_seconds=sum([x.get('durationInMinutes', 0) * 60 for x in sg['legs']]),
                # excl_connection_time_in_seconds=sg['legs'][0]['connectionTimeInMinutes'] * 60,
                excl_connection_time_in_seconds=sum([x.get('connectionTimeInMinutes', 0) * 60 for x in sg['legs']]),
            )
            segs.append(temp_seg)

        air_bound = AirBound(
            engine='AA',
            excl_duration_in_all_in_seconds=r['durationInMinutes'] * 60,
            stops=r['stops'],
            segments=segs,
            price=prices
        )
        results.append(air_bound)
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
            'flight_code': '-'.join([x['flight_code'] for x in segs]),
            'aircraft': '-'.join([str(x['aircraft']) for x in segs]),
            'from_to': ', '.join([x['departure'] + '-' + x['arrival'] for x in segs]),
            'departure_time': convert_datetime(segs[0]['departure_time']),
            'arrival_time': convert_datetime(segs[-1]['arrival_time']),
        }
        prices = result['price']
        prices_filtered = filter_price(prices, price_filter)
        #  如果所有票价均已被过滤，那么直接进入下一组循环。
        if len(prices_filtered) == 0:
            continue
        for pf in prices_filtered:
            prices_single = {
                'cabin_class': pf['cabin_class'],
                'quota': pf['quota'],
                'miles': convert_miles(pf['miles']),
                'cash': convert_cash(pf['cash'], currency=pf['currency']),
                'is_mix': pf['is_mix'],
                'mix_detail': pf['mix_detail'],
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
        width_dict = {}
        for col in df.columns.tolist():
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),  # len of largest item
                len(str(series.name))  # len of column name/header
            )) * 1.2 + 1
            width_dict[col] = max_len
        sf = StyleFrame(df, styler_obj=Styler())
        sf.set_column_width_dict(width_dict)
        writer = sf.to_excel('output.xlsx', row_to_add_filters=0)
        writer.save()
        print('Success! Please check the output excel file.')


def results_to_dash_table(results):
    df = pd.DataFrame(results)
    return df.to_dict('records')
