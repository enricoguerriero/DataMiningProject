from entities.actual_route import ActualRoute
from entities.preferences import Preferences
from entities.standard_route import StandardRoute
from utils.functions_pref import get_actual_routes_per_driver


def get_drivers_preferences(actual_routes: list[ActualRoute], driver: str = "") -> dict[str, Preferences]:
    preferences_per_driver = {}

    if driver == "":
        actual_routes_per_driver = get_actual_routes_per_driver(actual_routes)
        for driver_name in actual_routes_per_driver.keys():
            driver_data = actual_routes_per_driver[driver_name]
            preferences_per_driver[driver_name] = Preferences(driver_data, 0.2, 1000)

    else:
        actual_routes_per_driver = get_actual_routes_per_driver(actual_routes, driver)
        driver_data = actual_routes_per_driver[driver]
        print(driver)
        preferences_per_driver[driver] = Preferences(driver_data, 0.2, 1000)
        print(preferences_per_driver)

    return preferences_per_driver


def get_similarity_per_driver(preferences_per_driver: dict[str, Preferences],
                              standard_routes: list[StandardRoute]) -> dict[str, dict[str, float]]:
    if len(standard_routes) < 5:
        raise ValueError("Minimum 5 standard routes needed to compute the recommended routes")
    similarity_per_driver = {}
    weight_list = [3, 3, 3, 10, 5, 10, 10, 1, 2, 1]  # weights to compute distance

    from utils.preferoute import preferoute_similarity
    for driver_name in preferences_per_driver.keys():
        driver_preferences = preferences_per_driver[driver_name]
        similarity_per_driver[driver_name] = {}
        for sr in standard_routes:
            similarity_per_driver[driver_name][sr.id] = preferoute_similarity(sr, driver_preferences, weights=weight_list)
    return similarity_per_driver


def get_top_five_per_driver(similarity_per_driver: dict[str, dict[str, float]]) -> list[dict[str, list[str]]]:
    top_five_per_driver = []
    for driver_name in similarity_per_driver:
        driver_similarities = similarity_per_driver[driver_name]
        sorted_sim = sorted(driver_similarities.items(), key = lambda x: x[1], reverse = True)[:5]
        top_five = {"driver": driver_name, "routes": [route[0] for route in sorted_sim]}
        top_five_per_driver.append(top_five)
    return top_five_per_driver