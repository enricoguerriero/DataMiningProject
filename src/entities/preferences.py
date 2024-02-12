import time
import utils.frequent_itemset as frequent_itemset
import utils.functions_pref as d
import math
from utils.functions_pref import extract_trips
from entities.actual_route import ActualRoute
from first_point import merch_per_city_counter
from itertools import chain
from entities.coordinate_system import CoordinateSystem


class Preferences:
    """contains the preferences of each driver"""

    def __init__(self, data: list[ActualRoute], threshold: float, buckets: int):
        self.driver = data[0].driver
        self.n_trip = d.mean_trip(data)  # int, trip medi per route
        self.type_merch_avg = d.mean_types(extract_trips(data))  # int, numero medio di classi di merce per trip
        self.n_merch_per_route = d.mean_quantities(extract_trips(data))  # int, numero medio di merce (quantità totale) portata per trip

        self.freq_city = d.total_city_counter(d.start_finish_count(data, 0), d.pass_through_city_count(extract_trips(data))) # dict(key = string, value = int), lista di città per cui è passato spesso
        self.freq_start = d.start_finish_count(data, 0)  # dict(key = string, value = int), lista di città da cui è partito spesso
        self.freq_finish = d.start_finish_count(data)  # dict(key = string, value = int), lista di città in cui è arrivato spesso
        self.freq_trip = d.trip_count(extract_trips(data))  # dict(key = tuple, value = int), lista di trip effettuati spesso
        self.freq_itemset_city = frequent_itemset.run_pcy(d.extract_destinations(data), n_buckets=buckets, t_hold=threshold,
                                                          start=time.time())  # dict(key = tuple, value = int), freq itemset di città
        self.freq_itemset_trip = frequent_itemset.run_pcy(d.extract_trips_path(data), n_buckets=buckets, t_hold=threshold,
                                                          start=time.time())  # dict(key = tuple(tuple), value = int), freq itemset di trip
        self.n_merch = d.count_merch(d.extract_merchandise_type(extract_trips(data)))  # dict(key = string, value = int), lista di merci che ha portato spesso

        self.freq_city = self.freq_city.most_common(math.ceil(self.n_trip) * 2)
        self.freq_start = self.freq_start.most_common(math.ceil(self.n_trip) + 1)
        self.freq_finish = self.freq_finish.most_common(math.ceil(self.n_trip) + 1)
        self.freq_trip = self.freq_trip.most_common(math.ceil(self.n_trip))
        self.freq_itemset_city = sorted(self.freq_itemset_city.items(), key=lambda item: item[1],
                                   reverse=True)[0:math.ceil(self.n_trip)]
        self.freq_itemset_trip = sorted(self.freq_itemset_trip.items(), key=lambda item: item[1],
                                   reverse=True)[0:math.ceil(self.n_trip)]
        self.n_merch = self.n_merch.most_common(math.ceil(self.type_merch_avg * 2))

        self.freq_city = self.tuple_to_dict(self.freq_city)
        self.freq_start = self.tuple_to_dict(self.freq_start)
        self.freq_finish = self.tuple_to_dict(self.freq_finish)
        self.freq_trip = self.tuple_to_dict(self.freq_trip)
        self.freq_itemset_city = self.tuple_to_dict(self.freq_itemset_city)
        self.freq_itemset_trip = self.tuple_to_dict(self.freq_itemset_trip)
        self.n_merch = self.tuple_to_dict(self.n_merch)

        freq_dest = d.pass_through_city_count(extract_trips(data)).most_common(math.ceil(self.n_trip) * 2)
        freq_dest = self.tuple_to_dict(freq_dest)

        city_list = [item for item in freq_dest]
        city_list.extend([item[1] for item in self.freq_trip])
        prov = [list(chain.from_iterable(trip_couple)) for trip_couple in self.freq_itemset_trip]

        city_list.extend([subitem for item in prov for subitem in item])

        city_set = CoordinateSystem(list(set(city_list)), all_merch=[], all_trip=[])

        self.n_merch_per_city = merch_per_city_counter(data, city_set, t_hold_n=math.ceil(self.type_merch_avg))


    def tuple_to_dict(self, data: list) -> dict:
        return_obj = {}
        for d in data:
            return_obj[d[0]] = d[1]
        return return_obj

