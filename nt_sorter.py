from typing import List, Dict


def sort_segs(origins: List[Dict], seg_sorter: Dict = None):
    if seg_sorter is None:
        seg_sorter = {
            'key': 'duration_in_all',
            'ascending': True
        }
    key = seg_sorter.get('key')
    if key is None:
        return origins
    elif key in ['duration_in_all', 'stops']:
        origins.sort(key=lambda x: x[key], reverse=not seg_sorter['ascending'])
        return origins
    elif key == 'departure_time':
        origins.sort(key=lambda x: x['segments'][0][key], reverse=not seg_sorter['ascending'])
        return origins
    elif key == 'arrival_time':
        origins.sort(key=lambda x: x['segments'][len(x['segments']) - 1][key],
                     reverse=not seg_sorter['ascending'])
        return origins
    else:
        return origins
