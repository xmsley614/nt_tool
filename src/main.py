import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import argparse
import os
import json

from aa_searcher import Aa_Searcher
from dl_searcher import Dl_Searcher
from ac_searcher import Ac_Searcher
from nt_models import CabinClass, PriceFilter
from nt_parser import results_to_excel, convert_aa_response_to_models, convert_dl_response_to_models, convert_ac_response_to_models
from nt_filter import filter_prices, filter_airbounds, AirBoundFilter
from nt_sorter import get_default_sort_options, sort_airbounds
from utils import date_range


def search_helper(ori: str, des: str, date: str, searcher, converter, cabin_class: Optional[List[str]] = None):
    print(f'search for {ori} to {des} on {date} @ {datetime.now().strftime("%H:%M:%S")}')
    # ac has cabin_class while aa and dl do not
    if not cabin_class:
        response = searcher.search_for(ori=ori, des=des, date=date)
    else:
        response = searcher.search_for(ori=ori, des=des, date=date, cabin_class=cabin_class)
    v1 = converter(response)
    return v1


def search(origins: List[str], 
            destinations: List[str], 
            start_dt: str, 
            end_dt: str, 
            airbound_filter: AirBoundFilter, 
            price_filter: PriceFilter,
            searcher,
            converter,
            out_file_dir: str,
            out_file_name: str,
            sleep_sec: Optional[int] = 0,
            cabin_class: Optional[List[str]] = None):
    dates = date_range(start_dt, end_dt)
    airbounds = []
    # ac has cabin_class while aa and dl do not
    sort_options = get_default_sort_options('Shortest trip')
    for ori in origins:
        for des in destinations:
            for date in dates:
                v1 = search_helper(ori=ori, des=des, date=date, searcher=searcher, converter=converter, cabin_class=cabin_class)
                airbounds.extend(v1)
                # if there are high volume of network requests, add time.sleep
                time.sleep(sleep_sec)
    airbounds = filter_airbounds(airbounds, airbound_filter)
    airbounds = filter_prices(airbounds, price_filter)
    airbounds = sort_airbounds(airbounds, sort_options) if not cabin_class else airbounds
    results = []
    for x in airbounds:
        results.extend(x.to_flatted_list())
    results_to_excel(results=results,out_file_dir=out_file_dir,out_file_name=out_file_name)


def prepare_filter(input_dic: Dict):
    preferred_classes = [ CabinClass(single_preferred_class) for single_preferred_class in input_dic['preferred_classes']]
    #  cabin class removed, pls use price filter.
    airbound_filter = AirBoundFilter(
        max_stops=input_dic['max_stops'],
        airline_include=input_dic['airline_include'],
        airline_exclude=input_dic['airline_exclude'],
    )
    price_filter = PriceFilter(
        min_quota=input_dic['min_quota'],
        max_miles_per_person=input_dic['max_miles_per_person'],
        preferred_classes=preferred_classes,
        mixed_cabin_accepted=input_dic['mixed_cabin_accepted']
    )
    return airbound_filter, price_filter


def get_input_json(path_to_json_input: str):
    with open(path_to_json_input, "r") as input_file:
        input_dic = json.load(input_file)
    return input_dic


def use_aa_wrapper(args):
    input_dic = get_input_json(args.input_file)
    airbound_filter, price_filter = prepare_filter(input_dic)
    search(origins = input_dic['origins'], 
            destinations = input_dic['destinations'], 
            start_dt = input_dic['start_dt'], 
            end_dt = input_dic['end_dt'], 
            airbound_filter = airbound_filter, 
            price_filter = price_filter,
            searcher = Aa_Searcher(),
            converter = convert_aa_response_to_models,
            out_file_dir = args.output_dir,
            out_file_name = f'aa_result-{input_dic["start_dt"]}-{input_dic["end_dt"]}.xlsx',
            sleep_sec = 0)


def use_dl_wrapper(args):
    input_dic = get_input_json(args.input_file)
    airbound_filter, price_filter = prepare_filter(input_dic)
    search(origins = input_dic['origins'], 
            destinations = input_dic['destinations'], 
            start_dt = input_dic['start_dt'], 
            end_dt = input_dic['end_dt'], 
            airbound_filter = airbound_filter, 
            price_filter = price_filter,
            searcher = Dl_Searcher(),
            converter = convert_dl_response_to_models,
            out_file_dir = args.output_dir,
            out_file_name = f'dl_result-{input_dic["start_dt"]}-{input_dic["end_dt"]}.xlsx',
            sleep_sec = 0)


def use_ac_wrapper(args):
    input_dic = get_input_json(args.input_file)
    airbound_filter, price_filter = prepare_filter(input_dic)
    search(origins = input_dic['origins'], 
            destinations = input_dic['destinations'], 
            start_dt = input_dic['start_dt'], 
            end_dt = input_dic['end_dt'], 
            airbound_filter = airbound_filter, 
            price_filter = price_filter,
            cabin_class = input_dic["cabin_class"],
            searcher = Ac_Searcher(),
            out_file_dir = args.output_dir,
            out_file_name = f'ac_result-{input_dic["start_dt"]}-{input_dic["end_dt"]}.xlsx',
            converter = convert_ac_response_to_models,
            sleep_sec = 0)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    use_aa_parser = subparsers.add_parser('use_aa')
    use_aa_parser.add_argument('--input_file',type=str)
    use_aa_parser.add_argument('--output_dir',type=str)
    use_aa_parser.set_defaults(func=use_aa_wrapper)

    use_dl_parser = subparsers.add_parser('use_dl')
    use_dl_parser.add_argument('--input_file',type=str)
    use_dl_parser.add_argument('--output_dir',type=str)
    use_dl_parser.set_defaults(func=use_dl_wrapper)

    use_ac_parser = subparsers.add_parser('use_ac')
    use_ac_parser.add_argument('--input_file',type=str)
    use_ac_parser.add_argument('--output_dir',type=str)
    use_ac_parser.set_defaults(func=use_ac_wrapper)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()