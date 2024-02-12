# imports
import time
from entities.standard_route import StandardRoute
from entities.actual_route import ActualRoute
from second_point import get_drivers_preferences, get_similarity_per_driver, get_top_five_per_driver
from utils.functions import (get_actual_routes, get_first_output_path, get_second_output_path, get_third_output_path,
                             save_run_parameters, get_standard_routes, json_writer)
from utils.route_generator import data_generation
from entities.preferences import Preferences
from third_point import generate_trips, generate_path


global_start = int(round(time.time() * 1000))
# save_run_parameters()
# start = int(round(time.time() * 1000))
# data_generation()
# end = int(round(time.time() * 1000))
# print(f"routes generated in {end - start} milliseconds\n")


start = int(round(time.time() * 1000))
standard_routes = get_standard_routes()
actual_routes = get_actual_routes()
end = int(round(time.time() * 1000))
print(f"data fetched in {end - start} milliseconds\n")


start = int(round(time.time() * 1000))
# computing a dictionary with keys the names of the drivers and values list of ActualRoute
preferences_per_driver = get_drivers_preferences(actual_routes)
end = int(round(time.time() * 1000))
print(f"preferences generated in {end - start} milliseconds\n")

# Function: first output generator

def recommended_standard_route_generator(actual_routes: list[ActualRoute],
                                         standard_routes: list[StandardRoute]) -> None:
    '''
    Function for output 1:
    generates a set of recommended standard route wrote in a json file (no output)
    recommended standard route are based only on actual route
    '''

    # pyspark session:
    import findspark
    from pyspark.sql import SparkSession
    findspark.init()
    spark = SparkSession.builder.master("local").appName(name="PySpark for clustering").getOrCreate()

    # import functions
    from first_point import create_space, write_coordinates, create_clusters, build_centers, normalize_cluster_centers, \
        build_result, parameters_extraction

    parameters = parameters_extraction(standard_routes=standard_routes)

    # creation of the space
    space = create_space(actual_routes=actual_routes)

    # writing coordinates of every actual routes (according to the space) on a .csv file
    write_coordinates(actual_routes=actual_routes, space=space)

    # creation of a k-means clustering model
    model = create_clusters(actual_routes=actual_routes, n_standard_route=parameters["n_standard_route"], space=space,
                            spark=spark)

    # find centers of the model
    centers = build_centers(model=model, space=space)

    # normalize centers
    norm_centers = normalize_cluster_centers(cluster_centers=centers, actual_routes=actual_routes, model=model,
                                             space=space, spark=spark)

    # convert normalized centers in recommended standard route
    recommended_standard_route = build_result(normalized_centers=norm_centers, actual_routes=actual_routes,
                                              model=model, spark=spark)

    json_writer(recommended_standard_route, get_first_output_path())

    spark.stop()


def driver_preferences_generator(pref_dict: dict[str, Preferences]):

    # get similarity values for every driver for every standard route
    similarity_per_driver = get_similarity_per_driver(pref_dict, standard_routes)

    # for each driver sort similarity and write results
    top_five_per_driver = get_top_five_per_driver(similarity_per_driver)

    json_writer(top_five_per_driver, get_second_output_path())


def driver_ideal_route(pref_dict: dict[str, Preferences]):
    result = []

    for driver in pref_dict:
        result.append(generate_trips(generate_path(pref_dict[driver]), pref_dict[driver]))

    json_writer(result, get_third_output_path())


start = int(round(time.time() * 1000))
recommended_standard_route_generator(actual_routes, standard_routes)
end = int(round(time.time() * 1000))
print(f"\nfirst output in {end - start} milliseconds")

start = int(round(time.time() * 1000))
driver_preferences_generator(preferences_per_driver)
end = int(round(time.time() * 1000))
print(f"\nsecond output in {end - start} milliseconds")

start = int(round(time.time() * 1000))
driver_ideal_route(preferences_per_driver)
end = int(round(time.time() * 1000))
print(f"\nthird output in {end - start} milliseconds")

global_end = int(round(time.time() * 1000))
print(f"\ntotal time execution: {global_end - global_start} milliseconds")
