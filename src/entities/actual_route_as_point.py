from entities.actual_route import ActualRoute
from entities.coordinate_system import CoordinateSystem


class ActualRouteAsPoint:

    def __init__(self, ar: ActualRoute, space: CoordinateSystem) -> None:
        self.space = space
        v1 = [1 if city in ar.extract_city() else 0 for city in space.all_city_vec]
        v2 = [ar.extract_merch().quantity if merch in ar.extract_merch().item else 0 for merch in space.all_merch]
        v3 = [1 if trip in ar.route else 0 for trip in space.all_trip]
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.coordinates = v1 + v2 + v3