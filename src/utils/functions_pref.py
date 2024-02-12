import collections
import statistics
from entities.actual_route import ActualRoute
from entities.trip import Trip


def get_actual_routes_per_driver(actual_routes: list[ActualRoute], driver: str = "") -> dict[str, list[ActualRoute]]:
    routes_by_driver = {}

    if driver == "":
        for route in actual_routes:
            driver = route.driver
            routes_by_driver.setdefault(driver, []).append(route)

    else:
        for route in actual_routes:
            if driver == route.driver:
                routes_by_driver.setdefault(driver, []).append(route)

    return routes_by_driver


def extract_drivers(var: dict[str, ActualRoute]):
    """giver a set of routes, it extracts the drivers who have driven that routes. Used to extract data by driver"""
    return list(var.keys())


def count_occurrences(obj, spec, spec2=None):
    """counts how many times a specific object appears in a route and puts the value in a dictionary.

    Requires a trip (obj) and a specification (e.g. city_from) as input. If both city_from and city_to are passed,
    it counts how many times that trip has been performed"""
    occ = {}
    if spec2 is None:
        for item in obj:
            element = item.spec
            occ[element] = occ.get(element, 0) + 1
    else:
        for item in obj:
            element = [item.spec, item.spec2]
            element = tuple(element)
            occ[element] = occ.get(element, 0) + 1

    return occ


def extract_trips(var: list[ActualRoute]):
    """extracts the single trips from a set of routes"""
    trips = []
    for act_route in var:  # actual route
        for trip in act_route.route:
            trips.append(trip)

    return trips


def mean_trip(var: list[ActualRoute]):
    """computes the mean number of trips"""
    return len(extract_trips(var))/len(var)


def pass_through_city_count(trips: list[Trip]):
    """computes how many times a city has been visited in total, excluding starting point"""
    result = [item.city_to for item in trips]

    return collections.Counter(result)


def start_finish_count(var: list[ActualRoute], s_or_f=1):
    """computes the number of times a driver starts or finish from a given city

    s_or_f determines if it returns the cities where he started or the cities where he finished, s or 0 indicates
    start otherwise it's finish (default). Requires a list of actual routes as input."""
    result = []
    for act_route in var:
        "if looking for start"
        if s_or_f == 0 or s_or_f == 's':
            result.append(act_route.route[0].city_from)
            "if looking for finish"
        else:
            result.append(act_route.route[-1].city_to)

    return collections.Counter(result)


def total_city_counter(counter1: collections.Counter, counter2: collections.Counter):
    """Returns the total number of times a city has been touched, requires as input two outputs of the functions
    start_finish_count(data,0) and pass_through_city_count(extract_trips(data))"""
    return counter1 + counter2


def trip_count(trips: list[Trip]):
    """computes the number of times a specific trip has been traveled"""
    result = [(item.city_from, item.city_to) for item in trips]
    return collections.Counter(result)


def extract_destinations(var: list[ActualRoute]):
    """given a set of routes, it extracts the cities that were passed at least once, divided by route.

    Its output is a list of lists. Used for freq_itemset."""
    res = [act_route.extract_city() for act_route in var]

    return res


def extract_trips_path(var: list[ActualRoute]):
    """given a set of routes, it extracts the trips that were traveled at least once, divided by route.

        Its output is a list of lists of tuples"""
    res = [act_route.trip_without_merch() for act_route in var]
    return res


def extract_merchandise(trips: list[Trip]):
    """Returns a dictionary merchandise divided by trip (list of dictionaries)"""

    return [{key: value for key, value in zip(item.merchandise.item, item.merchandise.quantity)} for item in trips]


def extract_merchandise_type(trips: list[Trip]):
    """Returns all types of merchandise brought, divided by trip.

    the output is a list of lists. Used in frequent itemset"""
    return [trip.merchandise.item for trip in trips]


def mean_types(trips: list[Trip]):
    """Computes the mean of how many kinds of merch a driver has transported in a trip"""

    count = 0
    for items in extract_merchandise(trips):
        count += len(items)

    return count/len(extract_merchandise(trips))


def count_merch(merch_type: list[list[str]]):
    """computes the number of times a specific merch has been transported, for every merch item.

    Pass as parameters result of the function extract_merchandise_type"""
    res = [item for itemset in merch_type for item in itemset]
    return collections.Counter(res)


def mean_quantities(trips: list[Trip]):
    """returns the mean quantities of merch that the driver transports in a trip"""

    res = [sum(list(item.values())) for item in extract_merchandise(trips)]
    return statistics.mean(res)

