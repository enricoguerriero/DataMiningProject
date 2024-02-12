import numpy as np

class CoordinateSystem:

    def __init__(self, all_city_vec: list[str], all_merch: list[str], all_trip: list[str]) -> None:
        self.dimensions = len(all_city_vec) + len(all_merch) + len(all_trip)
        self.all_city_vec = all_city_vec
        self.all_merch = all_merch
        self.all_trip = all_trip
        self.origin = np.zeros(self.dimensions)