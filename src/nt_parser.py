from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

import pandas as pd
import requests
from styleframe import StyleFrame, Styler

from nt_models import Pricing, Segment, AirBound, CabinClass


def convert_miles(miles: int) -> str:
    return str(miles / 1000) + 'k'


def calculate_ac2_duration(duration_str: str):
    pattern = r'(?:(\d+)h)?\s*(?:(\d+)m)?'
    match = re.match(pattern, duration_str)

    if match:
        hours = int(match.group(1) or 0)  # 如果小时数未匹配到，则默认为0
        minutes = int(match.group(2) or 0)  # 如果分钟数未匹配到，则默认为0
        # 计算总秒数
        total_seconds = hours * 3600 + minutes * 60
        return total_seconds
    else:
        raise ValueError("Invalid time string format.")


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


def calculate_aa_mix_by_segment(target_cabin_class: CabinClass, duration_list: List[timedelta],
                                cabin_exist_list: List[List[CabinClass]]):
    total_duration = sum([x.total_seconds() for x in duration_list])
    percentage_list = [x.total_seconds() / total_duration for x in duration_list]
    actual_cabin_list = []
    for x in cabin_exist_list:
        x.sort(reverse=True)
        cabin_equal_or_lower_list = [v for v in x if target_cabin_class >= v]
        if len(cabin_equal_or_lower_list) == 0:
            #  no results satisfied, use the first element of list.
            actual_cabin_list.append(x[0])
        else:
            actual_cabin_list.append(cabin_equal_or_lower_list[0])
    if all([x == target_cabin_class for x in actual_cabin_list]):
        is_mix = False
        mix_detail = 'N/A'
    else:
        is_mix = True
        mix_detail = '+'.join(str(round(percentage_list[x] * 100, 0)) + '%' + actual_cabin_list[x]
                              for x in range(len(duration_list)))
    return is_mix, mix_detail


def calculate_dl_price_info(cabin_class_list: List[CabinClass], duration_list: List[int]):
    if len(cabin_class_list) == 1:
        cabin_class = cabin_class_list[0]
        is_mix = False
        mix_detail = 'N/A'
    elif all([x == cabin_class_list[0] for x in cabin_class_list]):
        cabin_class = cabin_class_list[0]
        is_mix = False
        mix_detail = 'N/A'
    else:
        all_duration = sum(duration_list)
        longest_duration_index = duration_list.index(max(duration_list))
        percentage_list = [round(100 * x / all_duration, 0) for x in duration_list]
        is_mix = True
        cabin_class = cabin_class_list[longest_duration_index]
        mix_detail = '+'.join(str(percentage_list[x]) + '%' + cabin_class_list[x] for x in range(len(percentage_list)))
    return cabin_class, is_mix, mix_detail


def calculate_dl_cabin_list(cabins_json: List[Dict]) -> List[CabinClass]:
    result = []
    booking_code_to_cabin_dict = {
        'X': 'Y',
        'O': 'J',
        'A': 'F',
    }
    for cb in cabins_json:
        if 'deltaCabinCode' in cb.keys():
            if cb['deltaCabinCode'] == 'C':
                # International Delta One Cabin Code
                result.append(CabinClass('F'))
            elif cb['deltaCabinCode'] == 'F':
                # International Delta One Cabin Code
                result.append(CabinClass('J'))
            else:
                result.append(CabinClass(cb['deltaCabinCode']))
        elif cb['bookingCode'] in booking_code_to_cabin_dict.keys():
            result.append(CabinClass(booking_code_to_cabin_dict[cb['bookingCode']]))
        elif 'ECONOMY' in cb['cabinName'].upper():
            result.append(CabinClass('Y'))
        elif 'BUSINESS' in cb['cabinName'].upper() \
                or 'Upper Class'.upper() in cb['cabinName'].upper():
            result.append(CabinClass('J'))
        elif 'FIRST' in cb['cabinName'].upper():
            result.append(CabinClass('F'))
        elif 'PREMIUM' in cb['cabinName'].upper():
            result.append(CabinClass('W'))
        else:
            raise ValueError('Cabin name error. Cabin detail:', cabins_json)
    return result


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
                            excl_miles=pr['airOffer']['milesConversion']['convertedMiles']['base'],
                            excl_cash_in_base_unit=pr['airOffer']['milesConversion']['convertedMiles'][
                                                       'totalTaxes'] / 100,
                            excl_currency='CAD',
                            is_mix=pr.get('isMixedCabin', False),
                            mix_detail=convert_mix(pr['availabilityDetails']) if pr.get('isMixedCabin',
                                                                                        False) else "N/A"
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


def convert_ac_response_to_models2(response: requests.Response) -> List:
    """
    Convert response from searcher request.
    param response: Response of searcher request.
    :return: List of nested json. Each json means an itinerary.
    """
    if response.status_code != 200:
        return list()
    else:
        response_json = response.json()
        temp1 = response_json.get('data', {}).get('getFareRedemption', {}).get('bound',
                                                                               []) if response_json is not None else {}
        air_bounds_json = temp1[0]['boundSolution'] if len(temp1) > 0 else []
        results = []
        saver_class_list = ['X', 'I', 'A']
        for r in air_bounds_json:
            r = dict(r)
            is_ac_flight = 'AC' in r['carrierType']
            print(r['carrierType'], is_ac_flight)
            prices_raw = r['fare']['cabins']
            segs_raw = [rr for rr in r['flightSegments']]
            prices = []
            segs = []
            for sg in segs_raw:
                temp_seg = Segment(
                    flight_code=sg['airline']['operatingCode'] + sg['flightNumber'],
                    aircraft=sg['equipmentType']['aircraftCode'],
                    departure=sg['originAirport'],
                    excl_departure_time=sg['scheduledDepartureDateTime'],
                    arrival=sg['destinationAirport'],
                    excl_arrival_time=sg['scheduledArrivalDateTime'],
                    excl_duration_in_seconds=calculate_ac2_duration(sg['segmentDuration']),
                    excl_connection_time_in_seconds=0,
                )
                segs.append(temp_seg)

            for pr in prices_raw:
                # price_raw now means the lowest of every physical cabin
                # filter AC flight without saver class code
                # if pr['bookingClass']['marketingCode'] == 'AC' \
                #         and pr['bookingClass']['bookingClassCode'] not in saver_class_list:
                #     continue
                # else:
                print(pr)

                if pr["shortCabin"] == "Premium Econ.":
                    cabin_class = "W"
                elif pr["shortCabin"] == "First Class":
                    cabin_class = "F"
                else:
                    cabin_class = pr["shortCabin"]

                temp_pricing = Pricing(
                    cabin_class=CabinClass[cabin_class],
                    quota=9,  # no info from raw
                    excl_miles=pr['fareAvailable'][0]['redemptionBooking']['pointsPortion']['baseFarePoints'],
                    excl_cash_in_base_unit=pr['fareAvailable'][0]['redemptionBooking']['cashPortion']['taxesTotal'],
                    excl_currency='CAD',
                    is_mix=False,
                    mix_detail='N/A'
                )
                prices.append(temp_pricing)

            air_bound = AirBound(
                engine='AC',
                excl_duration_in_all_in_seconds=calculate_ac2_duration(r['durationTotal']),
                stops=int(r['segmentCount']) - 1,
                segments=segs,
                price=prices
            )
            print(air_bound)
            results.append(air_bound)
        return results


def convert_aa_response_to_models(response: requests.Response) -> List:
    if response.status_code != 200:
        return []
    else:
        response_json = response.json()
        air_bounds_json = response_json.get('slices', []) if response_json is not None else []
        aa_saver_max_miles = 3 * min(
            int((response_json.get('utag', {}) if response_json is not None else {}).get('lowest_award_selling_miles',
                                                                                         33333)), 33333)
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
        segs_raw = [rr for rr in r['segments']]
        segs = []
        for sg in segs_raw:
            temp_seg = Segment(
                flight_code=sg['flight']['carrierCode'] + sg['flight']['flightNumber'],
                aircraft=sg['legs'][0]['aircraft']['code'],
                departure=sg['origin']['code'],  # TODO limit the str to only 3 chars
                excl_departure_time=sg['departureDateTime'],
                excl_cabin_exist=list(set([cabin_class_dict[x['cabinType']] for x in sg['legs'][0]['productDetails']])),
                arrival=sg['destination']['code'],
                excl_arrival_time=sg['arrivalDateTime'],
                # excl_duration_in_seconds=sg['legs'][0]['durationInMinutes'] * 60,
                excl_duration_in_seconds=sum([x.get('durationInMinutes', 0) * 60 for x in sg['legs']]),
                # excl_connection_time_in_seconds=sg['legs'][0]['connectionTimeInMinutes'] * 60,
                excl_connection_time_in_seconds=sum([x.get('connectionTimeInMinutes', 0) * 60 for x in sg['legs']]),
            )
            segs.append(temp_seg)
        is_aa_flight = any(['AA' in sg.flight_code for sg in segs])
        prices_raw = [rr['cheapestPrice'] for rr in r['productPricing']]
        prices = []
        for pr in prices_raw:
            # skip dynamic pricing of aa with an extremely high cost
            if is_aa_flight and pr['perPassengerAwardPoints'] > aa_saver_max_miles:
                # print("3 times more")
                continue
            if pr['extendedFareCode'] != '':
                temp_pricing = Pricing(
                    cabin_class=cabin_class_dict[pr['productType']],
                    quota=convert_aa_quota(pr['seatsRemaining']) if pr['extendedFareCode'] != '' else 0,
                    excl_miles=pr['perPassengerAwardPoints'],
                    excl_cash_in_base_unit=pr['perPassengerTaxesAndFees']['amount'],
                    excl_currency=pr['perPassengerTaxesAndFees']['currency'],
                )
                duration_list = [x.excl_duration_in_seconds for x in segs]
                cabin_exist_list = [x.excl_cabin_exist for x in segs]
                is_mix, mix_detail = calculate_aa_mix_by_segment(CabinClass(temp_pricing.cabin_class), duration_list,
                                                                 cabin_exist_list)
                temp_pricing.is_mix = is_mix
                temp_pricing.mix_detail = mix_detail
                prices.append(temp_pricing)
            else:
                continue

        air_bound = AirBound(
            engine='AA',
            excl_duration_in_all_in_seconds=r['durationInMinutes'] * 60,
            stops=r['stops'],
            segments=segs,
            price=prices
        )
        results.append(air_bound)
    return results


def convert_dl_response_to_models(response: requests.Response) -> List:
    if response.status_code != 200:
        return []
    else:
        response_json = response.json()
        air_bounds_json = response_json.get('itineraries', []) if response_json is not None else []
    results = []
    price_base = 0
    try:
        for r in air_bounds_json:
            r = dict(r)
            segs_raw = r['slice']['flights']
            segs = []
            for sg in segs_raw:
                temp_seg = Segment(
                    flight_code=sg['marketAirline']['code'] + sg['flightNumber'],
                    aircraft=sg['aircraftCode'],
                    departure=sg['origin']['airportCode'],  # TODO limit the str to only 3 chars
                    excl_departure_time=sg['departureDate'] + 'T' + sg['departureTime'],
                    arrival=sg['destination']['airportCode'],
                    excl_arrival_time=sg['arrivalDate'] + 'T' + sg['arrivalTime'],
                    excl_duration_in_seconds=sg['duration']['totalTimeInMinutes'] * 60,
                    excl_connection_time_in_seconds=sg.get('layover', {}).get('duration', {}).get('totalTimeInMinutes',
                                                                                                  0) * 60,
                )
                segs.append(temp_seg)
            prices_raw = r['fares']
            prices = []
            for pr in prices_raw:
                if pr.get('seatsRemaining', False):
                    if price_base == 0:
                        price_base = min(int(pr['fare']['totalPriceForOnePassenger']['miles']), 35000)
                        # print('price_base', price_base)
                    cabin_list = calculate_dl_cabin_list(pr['cabins'])
                    duration_list = [x['duration']['totalTimeInMinutes'] * 60 for x in segs_raw]
                    cabin_class, is_mix, mix_detail = calculate_dl_price_info(cabin_list, duration_list)
                    temp_pricing = Pricing(
                        cabin_class=cabin_class,
                        quota=pr['seatsRemaining'],
                        excl_miles=pr['fare']['totalPriceForOnePassenger']['miles'],
                        excl_cash_in_base_unit=pr['fare']['totalPriceForOnePassenger']['currency']['roundedAmount'],
                        excl_currency=pr['fare']['totalPriceForOnePassenger']['currency']['code'],
                        is_mix=is_mix,
                        mix_detail=mix_detail
                    )
                    multiplier = {
                        CabinClass.F: 4.5,
                        CabinClass.J: 3.5,
                        CabinClass.W: 2.5,
                        CabinClass.Y: 2
                    }
                    if temp_pricing.excl_miles > price_base * multiplier[temp_pricing.cabin_class]:
                        # filter the extremely high miles pricing
                        # print('result dropped', temp_pricing)
                        continue
                    prices.append(temp_pricing)
                else:
                    continue

            air_bound = AirBound(
                engine='DL',
                excl_duration_in_all_in_seconds=r['trip'][0]['totalTripTime']['totalTimeInMinutes'] * 60,
                stops=r['trip'][0]['stopCount'],
                segments=segs,
                price=prices
            )
            results.append(air_bound)
    except Exception as e:
        print(e.args)
    return results


def results_to_excel(results, out_file_dir: Optional[str] = '../output', out_file_name: Optional[str] = 'output.xlsx'):
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
        writer = sf.to_excel(f'{out_file_dir}/{out_file_name}', row_to_add_filters=0)
        writer.save()
        print('Success! Please check the output excel file.')


def results_to_dash_table(results):
    df = pd.DataFrame(results)
    return df.to_dict('records')
