import boto3

from dynamo import fetch_all_queries_from_dynamo
from process import find_air_bounds, send_notification, update_last_run_time
from aa_searcher import Aa_Searcher
from ac_searcher import Ac_Searcher
from dl_searcher import Dl_Searcher

LIMIT = 30
MIN_RUN_GAP = 4 * 3600

dynamodb = boto3.resource('dynamodb')
flight_queries_table = dynamodb.Table('flight_queries')
ses_client = boto3.client('ses')

aas = Aa_Searcher()
acs = Ac_Searcher()
dls = Dl_Searcher()


def handler(event, context):
    for q in fetch_all_queries_from_dynamo(flight_queries_table, LIMIT, MIN_RUN_GAP):
        for air_bound in find_air_bounds(aas, acs, dls, q):
            send_notification(air_bound, q, ses_client)
        update_last_run_time(flight_queries_table, q)

    return "success"
