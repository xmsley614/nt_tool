from typing import List

import requests
import json


class Aa_Searcher():
    def get_air_bounds(self, ori: str, des: str, date: str) -> requests.Response:
        headers = {
            "authority": "www.aa.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4",
            # "authorization": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhYS5jb20iLCJzdWIiOiJhaXJmYXJlLXNlYXJjaCIsImlhdCI6MTY3NzMzNTEyNywiZXhwIjoxNjc3MzM1MTU3fQ.XFFhP4DeneDmaxjBkvyV9K8krJjTQIekSQUJZnU0-2yNpUiInCW2tmj4v6qRl_j8p5ctJWtUHr-677SXg6eLjw",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.aa.com",
            "pragma": "no-cache",
            "referer": "https://www.aa.com/booking/choose-flights/1",
            "referrer-policy": "strict-origin-when-cross-origin",
            "sec-ch-ua": "\"Chromium\";v=\"110\", \"Not A(Brand\";v=\"24\", \"Microsoft Edge\";v=\"110\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50",
            # "x-cid": "387f59b6-abcf-45fc-ac90-45f2701eecda"
        }
        url = "https://www.aa.com/booking/api/search/itinerary"
        data = {
            "metadata": {
                "selectedProducts": [],
                "tripType": "OneWay",
                "udo": {}
            },
            "passengers": [
                {
                    "type": "adult",
                    "count": 1
                }
            ],
            "requestHeader": {
                "clientId": "AAcom"
            },
            "slices": [
                {
                    "allCarriers": True,
                    "cabin": '',
                    "departureDate": date,
                    "destination": des,
                    "destinationNearbyAirports": True,
                    "maxStops": None,
                    "origin": ori,
                    "originNearbyAirports": True
                }
            ],
            "tripOptions": {
                "searchType": "Award",
                "corporateBooking": False,
                "locale": "en_US"
            },
            "loyaltyInfo": None,
            "queryParams": {
                "sliceIndex": 0,
                "sessionId": "",
                "solu tionSet": "",
                "solutionId": ""
            }
        }
        response = requests.post(url, headers=headers, json=data)
        return response

    def search_for(self, ori: str, des: str, date: str):
        # if cabin_class is None:
        #     cabin_class = [
        #         "ECO",
        #         "PRE",
        #         "BIZ",
        #         "FIRST"
        #     ]
        # aa_searcher_cabin_class_dict = {
        #     "ECO": "COACH",
        #     "PRE": "PREMIUM_ECONOMY",
        #     "BIZ": "BUSINESS",
        #     "FIRST": "FIRST"
        # }
        # aa_searcher_cabin_class = [aa_searcher_cabin_class_dict[x] for x in cabin_class]

        # PREMIUM_ECONOMY is not identified in aa's api, so I remove it and force it return all cabins.
        ori = ori.upper()
        des = des.upper()
        aa_searcher_cabin_class = []
        try:
            r1 = self.get_air_bounds(ori, des, date)
            return r1
        except:
            # TODO: add log
            r1 = requests.Response
            r1.status_code = 404
            return requests.Response()
