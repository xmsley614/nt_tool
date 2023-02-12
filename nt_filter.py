def do_filter(origin, operator, value):
    if operator == '>':
        return origin > value
    elif operator == '>=':
        return origin >= value
    elif operator == '==':
        return origin == value
    elif operator == '<':
        return origin < value
    elif operator == '<=':
        return origin <= value
    elif operator == 'in':
        return origin in value


def filter_price(prices: list, price_filter: dict):

    if len(price_filter) == 0:
        return prices
    else:
        result = []
        for pr in prices:
            if all(
                    [do_filter(origin=pr[k], operator=v['operator'], value=v['value']) for k, v in price_filter.items()]
            ):
                result.append(pr)
        return result

if __name__ == '__main__':
    prices = [
        {
            'cabin_class': 'Y',
            'quota': 9,
            'miles': 100000,
            'cash': 65,
            'is_mix': False,

        },
        {
            'cabin_class': 'J',
            'quota': 2,
            'miles': 150000,
            'cash': 65,
            'is_mix': False,
        },
        {
            'cabin_class': 'F',
            'quota': 4,
            'miles': 250000,
            'cash': 65,
            'is_mix': True,
        },
    ]

    price_filter = {
        'quota': {
            'operator': '>',
            'value': 3
        },
        'cabin_class': {
            'operator': 'in',
            'value': ['J', 'PY', 'Y']
        },
        'is_mix': {
            'operator': '==',
            'value': False
        }
    }
    x = filter_price(prices, price_filter=price_filter)
    print(x)
