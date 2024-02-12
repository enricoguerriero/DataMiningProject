from entities.merchandise import Merchandise
from entities.trip import Trip


class StandardRoute:

    def __init__(self, data):
        self.id = data.get('id', '')
        self.route = [Trip(trip_data) for trip_data in data.get('route', [])]

    def extract_city(self) -> list[str]:
        if len(self.route) == 0:
            return []
        city_vec = [self.route[0].city_from]
        for i in range(len(self.route)):
            city_vec.append(self.route[i].city_to)
        return city_vec

    def trip_without_merch(self) -> list:
        new_route = [(trip.city_from, trip.city_to) for trip in self.route]
        return new_route

    def extract_merch(self) -> Merchandise:
        merch = Merchandise({})
        for trip in self.route:
            merch += trip.merchandise
        return merch
    
    def extract_merch_count(self, merch_label) -> int:
        counter = 0
        for trip in self.route:
            if merch_label in trip.merchandise.item:
                counter = counter + 1
        return counter
    
    def trip_string(self) -> list[str]:
        trips = []
        for trip in self.route:
            trip_string = "{city_from}:{city_to}".format(city_from = trip.city_from, city_to = trip.city_to)
            trips.append(trip_string)
        return trips
