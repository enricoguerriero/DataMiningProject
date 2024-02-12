import time
from entities.preferences import Preferences
from second_point import get_drivers_preferences, get_similarity_per_driver, get_top_five_per_driver
from utils.functions import (get_actual_routes, get_second_output_path, get_standard_routes, json_writer)

standard_routes = get_standard_routes()
actual_routes = get_actual_routes()
all_or_one = int(input("Type 1 to compute the output for every driver in the database, 0 to obtain data for a single driver: "))
start = int(round(time.time() * 1000))

if all_or_one:
    preferences_per_driver = get_drivers_preferences(actual_routes)
if not all_or_one:
    driver_name = input("Select driver: ")
    preferences_per_driver = get_drivers_preferences(actual_routes, str(driver_name))


def driver_preferences_generator(pref_dict: dict[str, Preferences]):

    # get similarity values for every driver for every standard route
    similarity_per_driver = get_similarity_per_driver(pref_dict, standard_routes)

    # for each driver sort similarity and write results
    top_five_per_driver = get_top_five_per_driver(similarity_per_driver)

    json_writer(top_five_per_driver, get_second_output_path())


driver_preferences_generator(preferences_per_driver)
end = int(round(time.time() * 1000))
print(f"\noutput in {end - start} milliseconds")
