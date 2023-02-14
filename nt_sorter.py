from typing import List, Dict


def sort_segs(origins: List[Dict], seg_sorter: Dict = None):
    if seg_sorter is None:
        seg_sorter = {
            'key': 'duration_in_all',
            'ascending': True
        }
    key = seg_sorter['key']
    if seg_sorter['key'] in ['duration_in_all', 'stops']:
        origins.sort(key=lambda x: x[key], reverse=not seg_sorter['ascending'])
        return origins
    elif seg_sorter['key'] == 'departure_time':
        origins.sort(key=lambda x: x['segments'][0][key], reverse=not seg_sorter['ascending'])
        return origins
    elif seg_sorter['key'] == 'arrival_time':
        origins.sort(key=lambda x: x['segments'][len(x['segments']) - 1][key],
                     reverse=not seg_sorter['ascending'])
        return origins
    else:
        return origins
