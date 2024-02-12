import time
from utils.functions import (get_actual_routes, get_third_output_path, json_writer)
from entities.preferences import Preferences
from third_point import generate_trips, generate_path
from second_point import get_drivers_preferences

actual_routes = get_actual_routes()

all_or_one = int(input("Type 1 to compute the output for every driver in the database, 0 to obtain data for a single driver: "))
start = int(round(time.time() * 1000))

if all_or_one:
    preferences_per_driver = get_drivers_preferences(actual_routes)
if not all_or_one:
    driver_name = input("Select driver: ")
    preferences_per_driver = get_drivers_preferences(actual_routes, str(driver_name))


def driver_ideal_route(pref_dict: dict[str, Preferences]):
    result = []

    for driver in pref_dict:
        result.append(generate_trips(generate_path(pref_dict[driver]), pref_dict[driver]))

    json_writer(result, get_third_output_path())


driver_ideal_route(preferences_per_driver)
end = int(round(time.time() * 1000))
print(f"\noutput in {end - start} milliseconds")
