import random
from entities.actual_route import ActualRoute
from entities.standard_route import StandardRoute
from second_point import get_drivers_preferences, get_similarity_per_driver
from utils.preferoute import preferoute_similarity
from third_point import generate_trips, generate_path
from entities.preferences import Preferences
from utils.functions import get_actual_routes, get_standard_routes
import numpy
import matplotlib.pyplot as plot


def test_ideal_route_driver(preferences: Preferences, ideal: dict):

    ideal['id'] = ideal['driver']
    stand_route = StandardRoute(ideal)
    weight_list = [3, 3, 3, 10, 5, 10, 10, 1, 2, 1]

    distance = preferoute_similarity(stand_route, preferences, weight_list)

    return distance


def data_adaptation(act_route_train: list[ActualRoute], act_route_test: list[ActualRoute]):
    pref_train = get_drivers_preferences(act_route_train)
    pref_final = get_drivers_preferences(act_route_test)

    ideal_route = {driver: generate_trips(generate_path(pref_train[driver]), pref_train[driver]) for driver in pref_train}

    result_train = {driver: test_ideal_route_driver(preference, ideal_route[driver])
                    for (driver, preference) in pref_train.items()}

    result_test = {driver: test_ideal_route_driver(preference, ideal_route[driver])
                   for (driver, preference) in pref_final.items()}

    return {key: result_train[key] - result_test[key] for key in result_train}


def mean_variation(test_result: dict):
    mean_value = numpy.mean(list(test_result.values()))

    plot.boxplot(list(test_result.values()))
    plot.title('Boxplot of Similarity Variation')
    plot.ylabel('Values')
    plot.grid(True, linestyle='--', alpha=0.5)
    plot.xticks([])
    plot.show()

    return mean_value


actual_routes = get_actual_routes()
actual_routes_train = random.sample(actual_routes, round(len(actual_routes) * 0.8))

print(mean_variation(data_adaptation(actual_routes_train, actual_routes)))
