import os
from .stationlist import StationList
from .servicebuilder import ServiceBuilder

def calculate_time(estimated, scheduled):
    if(estimated == "On time"):
        return scheduled
    else:
        return estimated

def get_calling_points(service_data):
    try:
        return service_data['subsequentCallingPoints']['callingPointList'][0]['callingPoint'];
    except KeyError as e:
        raise Exception("Failed to get calling points")

def get_destination(calling_points, destination_crs):
    return next(point for point in calling_points if point["crs"] == destination_crs)

def get_arrival_time(service_data, destination_crs):
    calling_points = get_calling_points(service_data);
    destination = get_destination(calling_points, destination_crs)
    scheduled_time = destination['st']
    estimated_time = destination['et']
    estimated_time = calculate_time(scheduled_time, estimated_time)

    return scheduled_time, estimated_time


def buildService(service_data, from_crs, to_crs):
    stationList = StationList()
    origin_name = stationList.get_station_name(from_crs)
    destination_name = stationList.get_station_name(to_crs)

    data = {}
    data['id'] = service_data.serviceID

    data['origin'] = {}
    data['origin']['name'] = origin_name
    data['origin']['crs'] = from_crs
    data['origin']['scheduled'] = service_data.std
    data['origin']['estimated'] = calculate_time(service_data.etd, service_data.std)

    data['destination'] = {}
    data['destination']['name'] = destination_name
    data['destination']['crs'] = to_crs
    data['destination']['scheduled'], data['destination']['estimated'] = get_arrival_time(service_data, to_crs)

    data['isCancelled'] = 0 if service_data.isCancelled is None else 1

    if service_data.platform is not None:
        data['platform'] = service_data.platform
    else:
        data['platform'] = ""

    return data


class TrainApp:
    def __init__(self, darwin_service):
        self.darwin_service = darwin_service
        return

    def sort_departures(self, departures):
        return sorted(departures, key=lambda k:k['origin']['scheduled'])

    def next_departures(self, from_crs, to_crs, number_of_departures):
        station_list = StationList()
        if not station_list.validate_crs(from_crs) or not station_list.validate_crs(to_crs):
            raise Exception("CRS code is invalid")

        departures = []

        response = self.darwin_service.load_departures(from_crs, to_crs, number_of_departures)
  
        if response.trainServices is not None:
            for service_data in response.trainServices.service:
                train_service = ServiceBuilder().build(service_data, from_crs, to_crs)
                departures.append(train_service)

        return departures
