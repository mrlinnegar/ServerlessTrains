from lib.trainapp import TrainApp
from lib.stationlist import StationList
from lib.darwinservice import DarwinService
from lib.utilities import extract_crs
from lib.utilities import build_response_object
from lib.utilities import time_to_integer
from lib.encoders import ServiceListEncoder

import json
import os

WSDL = os.environ['WSDL']
token = os.environ['DARWIN_TOKEN']


def stations(event, context):

    stationList = StationList()
    data = stationList.stations()
    body = json.dumps(data)
    response = build_response_object(200, body);
    return response


def next(event, context):
    response = {}
    try:
        station_list = StationList()
        number_of_departures = 4
        service = DarwinService(WSDL, token)

        from_crs, to_crs = extract_crs(event)
        
        departures = TrainApp(service).next_departures(from_crs, to_crs, number_of_departures)
    
        body = json.dumps(departures, cls=ServiceListEncoder)
        response = build_response_object(200, body)

    except Exception as e:
        body = str(e)
        response = build_response_object(500, body)

    finally:
        return response


def spread(event, context):
    try:
        
        service = DarwinService(WSDL, token)
        app = TrainApp(service)
        body = event['body']
        data = json.loads(body)
        number_of_departures = data['limit']
        if number_of_departures == 0:
            raise Exception("No limit specified")

        departures = []
        
        for origin in data['from']:
            for destination in data['to']:
                new_departures_data = app.next_departures(origin, destination, number_of_departures)
                departures = departures + new_departures_data
        
        sorted_departures = app.sort_departures(departures)

        data = [];

        for index, departure in enumerate(sorted_departures):
            if index < number_of_departures:
                departure = {
                    "o" : departure.origin.crs,
                    "d" : departure.destination.crs,
                    "s" : time_to_integer(departure.origin.time.scheduled),
                    "e" : time_to_integer(departure.origin.time.estimated),
                }
                data.append(departure)

        response = build_response_object(200, json.dumps(data))
    except Exception as e:
        body = str(e)
        response = build_response_object(500, body)
    finally:
        return response
