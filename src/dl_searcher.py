from typing import List

import requests
import json


class Dl_Searcher():
    def get_air_bounds(self, ori: str, des: str, date: str) -> requests.Response:
        headers = {
            "Host": "api.delta.com",
            "content-type": "application/json;charset=UTF-8",
            "tlioscnx": "Wi-Fi",
            "accept": "application/json",
            "x-app-route": "SL-RSB",
            "tliosloc": "gn=bookFlight: search results oneway&ch=booking",
            "x-offer-route": "SL-SHOP",
            "x-adapter": "mobile",
            "user-agent": "Fly Delta"
        }
        url = "https://api.delta.com/mwsb/service/shop"
        data = {
            "segments": [
                {
                    "origin": ori,
                    "departureDate": date,
                    "destination": des
                }
            ],
            "priceType": "Award",
            "constraints": [],
            "tripType": "ONE_WAY",
            "version": "2",
            "bestFare": "",
            "passenger": {
                "adultCount": "1"
            },
            "sortBy": "deltaBestMatch"
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, data=data)
        return response

    def search_for(self, ori: str, des: str, date: str):
        ori = ori.upper()
        des = des.upper()
        try:
            r1 = self.get_air_bounds(ori, des, date)
            return r1
        except:
            # TODO: add log
            r1 = requests.Response
            r1.status_code = 404
            return requests.Response()

if __name__ == '__main__':
    dl = Dl_Searcher()
    x = dl.search_for('YVR', 'NYC', '2023-06-06')
    print(x.text)