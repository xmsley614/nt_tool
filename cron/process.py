from datetime import timedelta
import time

from aa_searcher import Aa_Searcher
from ac_searcher import Ac_Searcher
from dl_searcher import Dl_Searcher
from dynamo import FlightQuery
from nt_models import CabinClass, AirBound
from nt_parser import convert_aa_response_to_models, convert_ac_response_to_models, \
    convert_dl_response_to_models


def match_query(air_bound: AirBound, q: FlightQuery):
    if q.max_stops is not None and air_bound.stops > q.max_stops:
        return False
    if q.max_duration and air_bound.excl_duration_in_all_in_seconds > timedelta(
            hours=int(q.max_duration)):
        return False
    if q.exact_airport and not (air_bound.from_to.startswith(q.origin) and
                                air_bound.from_to.endswith(q.destination)):
        return False

    for price in air_bound.price:
        if q.cabin_class and price.cabin_class != CabinClass.from_string(q.cabin_class):
            continue
        if q.num_passengers and price.quota < q.num_passengers:
            continue
        if air_bound.engine.upper() == "AA" and price.excl_miles <= q.max_aa_points:
            return True
        if air_bound.engine.upper() == "AC" and price.excl_miles <= q.max_ac_points:
            return True
        if air_bound.engine.upper() == "DL" and price.excl_miles <= q.max_dl_points:
            return True

    # Did not find any price in selected cabin.
    return False


def update_last_run_time(flight_queries_table, q):
    flight_queries_table.update_item(
        Key={
            "id": q.id
        },
        UpdateExpression="SET last_run = :last_run",
        ExpressionAttributeValues={
            ":last_run": int(time.time())
        }
    )


def send_notification(air_bound: AirBound, q: FlightQuery, ses_client):
    resp = ses_client.list_identities(IdentityType='EmailAddress')
    if not resp.get("Identities"):
        raise Exception("Cannot send notification because no ses verified identity exists")
    source_email = resp["Identities"][0]

    print(f"Sending email for {air_bound.to_cust_dict()}")
    ses_client.send_email(
        Source=source_email,
        Destination={
            'ToAddresses': [
                q.email,
            ],
        },
        Message={
            'Subject': {
                'Data': f'Reward Ticket Found for {q.origin}-{q.destination} on {q.date}'
            },
            'Body': {
                'Text': {
                    'Data': "\n".join([str(x) for x in air_bound.to_flatted_list()])
                }
            }
        }
    )


def find_air_bounds(aas: Aa_Searcher, acs: Ac_Searcher, dls: Dl_Searcher, q: FlightQuery):
    print(f'Search for {q}')

    air_bounds = []

    # Search from AA.
    if q.max_aa_points and q.max_aa_points > 0:
        response = aas.search_for(q.origin, q.destination, q.date)
        aa_air_bounds = convert_aa_response_to_models(response)
        air_bounds.extend(aa_air_bounds)

    # Search from AC.
    if q.max_ac_points and q.max_ac_points > 0:
        response = acs.search_for(q.origin, q.destination, q.date)
        ac_air_bounds = convert_ac_response_to_models(response)
        air_bounds.extend(ac_air_bounds)

    # Search from DL.
    if q.max_dl_points and q.max_dl_points > 0:
        response = dls.search_for(q.origin, q.destination, q.date)
        dl_air_bounds = convert_dl_response_to_models(response)
        air_bounds.extend(dl_air_bounds)

    # Process each result and send notification if found a match.
    for air_bound in air_bounds:
        if match_query(air_bound, q):
            yield air_bound
