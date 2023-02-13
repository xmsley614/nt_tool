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

