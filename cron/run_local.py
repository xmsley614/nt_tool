from datetime import date, timedelta
import random

from app import handler, flight_queries_table, aas, acs, dls
from process import find_air_bounds
from dynamo import FlightQuery

# This is the email that you want to receive notification.
# You need to verify it in SES first before using it.
EMAIL = "your_email@gmail.com"

# Test run Lambda function.
# handler(1, 1)

# Run search locally. You can also use this block to add routes in DynamoDB.
dry = False
start_date = date(2023, 12, 11)
end_date = date(2023, 12, 11)
for origin in {"ICN"}:
    for dest in {"PVG"}:
        cur_date = start_date
        while cur_date <= end_date:
            item = {
                "id": str(random.randint(0, 100000000)),
                "origin": origin,
                "destination": dest,
                "date": cur_date.isoformat(),
                "num_passengers": 1,
                "cabin_class": "ECO",
                "max_stops": 0,
                "max_duration": 5,
                "max_ac_points": 50000,
                "max_aa_points": 30000,
                "max_dl_points": 50000,
                "exact_airport": True,
                "email": EMAIL,
                "last_run": 0,
            }

            # Print results directly
            print(list(find_air_bounds(aas, acs, dls, FlightQuery(**item))))

            # Add query to DynamoDB
            # print(f"Adding {origin}-{dest} on {cur_date}")
            # if not dry:
            #     flight_queries_table.put_item(Item=item)



            # Update date for the next run. Do not comment this line.
            cur_date += timedelta(days=1)
