import hashlib
import hmac
import json
import datetime

import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth, getSignatureKey


class AWSRequestsAuth2(AWSRequestsAuth):
    def get_aws_request_headers(self, r, aws_access_key, aws_secret_access_key, aws_token):
        """
        Returns a dictionary containing the necessary headers for Amazon's
        signature version 4 signing process. An example return value might
        look like

            {
                'Authorization': 'AWS4-HMAC-SHA256 Credential=YOURKEY/20160618/us-east-1/es/aws4_request, '
                                 'SignedHeaders=host;x-amz-date, '
                                 'Signature=ca0a856286efce2a4bd96a978ca6c8966057e53184776c0685169d08abd74739',
                'x-amz-date': '20160618T220405Z',
            }
        """
        # Create a date for headers and the credential string
        t = datetime.datetime.utcnow()
        # t = t.replace(hour=18, minute=0, second=8)
        amzdate = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')  # Date w/o time for credential_scope

        canonical_uri = AWSRequestsAuth.get_canonical_path(r)

        canonical_querystring = AWSRequestsAuth.get_canonical_querystring(r)

        # Create the canonical headers and signed headers. Header names
        # and value must be trimmed and lowercase, and sorted in ASCII order.
        # Note that there is a trailing \n.
        canonical_headers = ('host:' + self.aws_host + '\n' +
                             'x-amz-date:' + amzdate + '\n')
        if aws_token:
            canonical_headers += 'x-amz-security-token:' + aws_token + '\n'

        # Create the list of signed headers. This lists the headers
        # in the canonical_headers list, delimited with ";" and in alpha order.
        # Note: The request can include any headers; canonical_headers and
        # signed_headers lists those that you want to be included in the
        # hash of the request. "Host" and "x-amz-date" are always required.
        signed_headers = 'host;x-amz-date'
        if aws_token:
            signed_headers += ';x-amz-security-token'

        # Create payload hash (hash of the request body content). For GET
        # requests, the payload is an empty string ('').
        body = r.body if r.body else bytes()
        try:
            body = body.encode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            # On py2, if unicode characters in present in `body`,
            # encode() throws UnicodeDecodeError, but we can safely
            # pass unencoded `body` to execute hexdigest().
            #
            # For py3, encode() will execute successfully regardless
            # of the presence of unicode data
            body = body

        payload_hash = hashlib.sha256(body).hexdigest()

        # Combine elements to create create canonical request
        canonical_request = (r.method + '\n' + '/graphql' + '\n' +
                             canonical_querystring + '\n' + canonical_headers +
                             '\n' + signed_headers + '\n' + payload_hash)

        # Match the algorithm to the hashing algorithm you use, either SHA-1 or
        # SHA-256 (recommended)
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = (datestamp + '/' + self.aws_region + '/' +
                            self.service + '/' + 'aws4_request')
        string_to_sign = (algorithm + '\n' + amzdate + '\n' + credential_scope +
                          '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest())

        # Create the signing key using the function defined above.
        signing_key = getSignatureKey(aws_secret_access_key,
                                      datestamp,
                                      self.aws_region,
                                      self.service)

        # Sign the string_to_sign using the signing_key
        string_to_sign_utf8 = string_to_sign.encode('utf-8')
        signature = hmac.new(signing_key,
                             string_to_sign_utf8,
                             hashlib.sha256).hexdigest()

        # The signing information can be either in a query string value or in
        # a header named Authorization. This code shows how to use a header.
        # Create authorization header and add to request headers
        authorization_header = (algorithm + ' ' + 'Credential=' + aws_access_key +
                                '/' + credential_scope + ', ' + 'SignedHeaders=' +
                                signed_headers + ', ' + 'Signature=' + signature)

        headers = {
            'Authorization': authorization_header,
            'x-amz-date': amzdate,
            'x-amz-content-sha256': payload_hash
        }
        if aws_token:
            headers['X-Amz-Security-Token'] = aws_token
        return headers


class Ac_Searcher2():
    def __init__(self):
        # pass
        self.get_aws_config()

    def get_aws_id(self):
        headers = {
            "Host": "cognito-identity.us-east-2.amazonaws.com",
            "accept": "*/*",
            "content-type": "application/x-amz-json-1.1",
            "x-amz-target": "AWSCognitoIdentityService.GetId",
            "accept-language": "zh-CN,zh-Hans;q=0.9",
            # "x-amz-date": "20230529T151356Z",
            "x-dynatrace": "MT_3_4_152475381787673_1-0_d0ab54df-6dc3-4fc4-bf15-38ce2539a422_34_18_158",
            "user-agent": "aws-sdk-iOS/2.27.15 iOS/15.5 en_CN aws-amplify-cli/0.1.0"
        }
        url = "https://cognito-identity.us-east-2.amazonaws.com/"
        data = '{"IdentityPoolId":"us-east-2:6659d286-8971-4231-bf50-ba720e7ba3e3"}'
        response = requests.post(url, headers=headers, data=data)
        # print(response.text)
        return response.json()['IdentityId']

    def get_aws_config(self):
        headers = {
            "Host": "cognito-identity.us-east-2.amazonaws.com",
            "accept": "*/*",
            "content-type": "application/x-amz-json-1.1",
            "x-amz-target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
            "accept-language": "zh-CN,zh-Hans;q=0.9",
            # "x-amz-date": "20230529T151358Z",
            "x-dynatrace": "MT_3_4_152475381787673_1-0_d0ab54df-6dc3-4fc4-bf15-38ce2539a422_0_19_169",
            "user-agent": "aws-sdk-iOS/2.27.15 iOS/15.5 en_CN aws-amplify-cli/0.1.0"
        }
        url = "https://cognito-identity.us-east-2.amazonaws.com/"
        data = {
            "IdentityId": self.get_aws_id()
        }
        response = requests.post(url, headers=headers, json=data)
        # print(response.text)
        r1 = response.json()
        self.access_key = r1['Credentials']['AccessKeyId']
        self.secret_key = r1['Credentials']['SecretKey']
        self.session_token = r1['Credentials']['SessionToken']

    def get_auth(self):
        return AWSRequestsAuth2(aws_access_key=self.access_key,
                                aws_secret_access_key=self.secret_key,
                                aws_host='lfs-mob.appsync.dbaas.aircanada.com',
                                aws_region='us-east-2',
                                aws_service='appsync',
                                aws_token=self.session_token)

    def get_air_bounds(self, ori: str, des: str, date: str, number_of_passengers: int):
        headers = {
            "Host": "akamai-gw.dbaas.aircanada.com",
            "content-type": "application/json",
            "accept": "*/*",
            # "accept-language": "zh-CN,zh-Hans;q=0.9",
            "user-agent": "aws-sdk-ios/3.5.0 AppSyncClient",
        }
        cookies = {
        }
        url = "https://akamai-gw.dbaas.aircanada.com/appsync/lfs"
        data = {
            "variables": {
                "uid": None,
                "numberOfRewards": "0",
                "pointOfSale": "ACMobile3",
                "fareBasisCode": "",
                "type": "OneWay",
                "timestamp": None,
                "selectionID": "",
                "currency": "CAD",
                "sessionID": "",
                "language": "en",
                "signature": None,
                "bounds": [
                    {
                        "origin": ori,
                        "departureDate": date,
                        "destination": des
                    }
                ],
                "benefitBalanceCode": "",
                "bookingClassCode": "",
                "passengers": {
                    "adult": number_of_passengers,
                    "passengerTotal": number_of_passengers,
                    "youth": 0,
                    "child": 0,
                    "infantLap": 0
                },
                "frequentFlyer": None
            },
            "query": "query GetFareRedemption($pointOfSale: String!, $currency: String!, $language: String!, $type: String!, $bounds: [SearchBoundInput]!, $passengers: PassengersInput!, $selectionID: String!, $bookingClassCode: String!, $fareBasisCode: String!, $frequentFlyer: String, $sessionID: String, $benefitBalanceCode: String, $numberOfRewards: String, $uid: String, $signature: String, $timestamp: String) {\n  getFareRedemption(pointOfSale: $pointOfSale, currency: $currency, language: $language, type: $type, bounds: $bounds, passengers: $passengers, selectionID: $selectionID, bookingClassCode: $bookingClassCode, fareBasisCode: $fareBasisCode, frequentFlyer: $frequentFlyer, sessionID: $sessionID, benefitBalanceCode: $benefitBalanceCode, numberOfRewards: $numberOfRewards, uid: $uid, signature: $signature, timestamp: $timestamp) {\n    __typename\n    searchInformation {\n      __typename\n      pointOfSale\n      currency\n      language\n      type\n      bounds {\n        __typename\n        origin\n        destination\n        departureDate\n      }\n      passengers {\n        __typename\n        adult\n        youth\n        child\n        infantLap\n        passengerTotal\n      }\n      sessionID\n    }\n    ac2uErrorsWarnings {\n      __typename\n      code\n      type\n      message\n    }\n    errors {\n      __typename\n      lang\n      context\n      systemService\n      systemErrorType\n      systemErrorCode\n      systemErrorMessage\n      friendlyCode\n      friendlyTitle\n      friendlyMessage\n      closeLabel\n      actions {\n        __typename\n        number\n        buttonLabel\n        action\n      }\n    }\n    bound {\n      __typename\n      boundSolution {\n        __typename\n        tripType\n        segmentCount\n        connectionCount\n        containsDirect\n        scheduledDepartureDateTime\n        scheduledArrivalDateTime\n        durationTotal\n        flightSegments {\n          __typename\n          segmentNumber\n          flightNumber\n          originAirport\n          originTerminal\n          destinationAirport\n          destinationTerminal\n          scheduledDepartureDateTime\n          scheduledArrivalDateTime\n          segmentDuration\n          stops {\n            __typename\n            stopAirport\n            disembarkationRequired\n          }\n          lastStop {\n            __typename\n            stopCode\n            stopLocation\n          }\n          equipmentType {\n            __typename\n            aircraftCode\n            aircraftName\n          }\n          airline {\n            __typename\n            operatingCode\n            operatingName\n            marketingCode\n            marketingName\n            userFriendlyCode\n            acOperated\n          }\n          departsEarly\n          stopCount\n          isTrainIndicator\n          isBusIndicator\n        }\n        connection {\n          __typename\n          connectionNumber\n          connectionAirport\n          startTime\n          endTime\n          connectionDuration\n          previousFlight {\n            __typename\n            previousFlightOperatorCode\n            previousFlightNumber\n          }\n          nextFlight {\n            __typename\n            nextFlightOperatorCode\n            nextFlightNumber\n          }\n          overNight\n          isAirportChange\n        }\n        fare {\n          __typename\n          cabins {\n            __typename\n            cabinCode\n            cabinName\n            shortCabin\n            fareAvailable {\n              __typename\n              bookingClass {\n                __typename\n                marketingCode\n                flightNumber\n                bookingClassCode\n                fareBasisCode\n                noOfSeats\n                alertLowSeats\n                comment\n                selectionID\n                meal {\n                  __typename\n                  mealCode\n                  mealName\n                }\n                segmentCabinName\n              }\n              fareFamily\n              shortFareFamily\n              refundable\n              percentageInSelectedCabin\n              promoApplicable\n              priorityRewardApplicable\n              revenueBooking {\n                __typename\n                baseFare\n                feesTotal\n                taxesTotal\n                fareTotal\n                fareTotalRounded\n              }\n              redemptionBooking {\n                __typename\n                cashPortion {\n                  __typename\n                  baseFare\n                  taxesTotal\n                  fareTotal\n                  fareTotalRounded\n                  taxesTotalRounded\n                  currencyCode\n                }\n                pointsPortion {\n                  __typename\n                  baseFarePoints\n                  taxesTotalPoints\n                  fareTotalPoints\n                  baseFarePointsRounded\n                  fareTotalPointsRounded\n                  pointsIndicator\n                  displayFormat {\n                    __typename\n                    displayPoints\n                    displayDollarAmount\n                    displayPointsIndicator\n                  }\n                }\n              }\n              isPureUpsell\n              mixedCabin {\n                __typename\n                mixedNumber\n                marketingCode\n                flightNumber\n                origin\n                destination\n                actualCabinCode\n                actualCabinName\n              }\n              submitReview {\n                __typename\n                segment {\n                  __typename\n                  selectionID\n                  bookingClassCode\n                  fareBasisCode\n                  departureDate\n                  arrivalDate\n                  origin\n                  destination\n                  flightNumber\n                  carrierCode\n                  fareBreakpoint\n                  stopCode\n                  stopCount\n                }\n              }\n              priceRequestInformation {\n                __typename\n                accountCode\n                acPromoInformation {\n                  __typename\n                  promoCode\n                  promoCodeType\n                  discountValue\n                  expiryDate\n                  promoCodeCurrency\n                }\n                acError {\n                  __typename\n                  errorFlag\n                  errorReason\n                  errorMessage\n                  errorCode\n                }\n              }\n            }\n          }\n        }\n        operatingDisclosure\n        carrierType\n      }\n      boundNumber\n      originAirport\n      destinationAirport\n      departureDate\n      cubaDestination\n      market\n      resultSummary {\n        __typename\n        cabinCode\n        cabinName\n        cabinShortName\n        uniqueResult\n        lowestFare\n        lowestFareRounded\n        lowestFareDisplayFormat\n        pointIndicatorDisplayFormat\n      }\n    }\n    benefits {\n      __typename\n      ticketAttributes {\n        __typename\n        fareFamily\n        marketingCarrierCode\n        carrierTypeBenefits\n        Attribute {\n          __typename\n          attributeNumber\n          name\n          description\n          icon\n          shortlist\n          assessment\n          value {\n            __typename\n            value\n          }\n          category {\n            __typename\n            name\n          }\n        }\n      }\n      productAttributes {\n        __typename\n        cabinCode\n        cabinName\n        shortCabin\n        marketingCarrierCode\n        Attributes {\n          __typename\n          attributeNumber\n          name\n          description\n          icon\n          shortlist\n          value {\n            __typename\n            value\n          }\n          category {\n            __typename\n            name\n          }\n        }\n      }\n      aircraftAttributes {\n        __typename\n        code\n        name\n        operatingCarrierCode\n        cabins {\n          __typename\n          cabinCode\n          cabinName\n          shortCabin\n          businessSeatType\n          Attributes {\n            __typename\n            attributeNumber\n            name\n            description\n            icon\n            shortlist\n            category {\n              __typename\n              name\n            }\n            value {\n              __typename\n              value\n            }\n          }\n        }\n      }\n    }\n    key\n    priorityRewards {\n      __typename\n      source\n      success\n      priorityRewardsApplicable\n      numberRequired\n      totalMatchingRewards\n      information {\n        __typename\n        friendlyName\n        benefitBalanceCode\n        count\n        nextExpiryDate\n        matching\n        bound\n      }\n      applied {\n        __typename\n        benefitBalanceCode\n        friendlyName\n        numberOfRewardsApplied\n        nextExpiryDate\n      }\n      submit {\n        __typename\n        benefitBalanceCode\n        numberOfRewardsApplied\n      }\n    }\n  }\n}"
        }

        response = requests.post(url, headers=headers, cookies=cookies, json=data, auth=self.get_auth())
        return response

    def search_for(self, ori: str, des: str, date: str, number_of_passengers: int = 1):
        ori = ori.upper()
        des = des.upper()
        if number_of_passengers <= 0 or number_of_passengers > 9:
            number_of_passengers = 1
        try:
            r1 = self.get_air_bounds(ori, des, date, number_of_passengers)
            return r1
        except:
            # TODO: add log
            r1 = requests.Response
            r1.status_code = 404
            return requests.Response()


if __name__ == '__main__':
    ac = Ac_Searcher2()
    r1 = ac.get_air_bounds('TYO', 'LAX', '2023-06-07', 1)
    print(r1.text)
