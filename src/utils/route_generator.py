# DATA GENERATION
import os
from dotenv import load_dotenv

from utils.functions import get_ar_path, get_sr_path, json_writer
load_dotenv()

import random, string

merchandise = []

# Functions for generation of standard routes

def provinces_reader(file_path="src/data/province.csv"):
    """
    Reads province names from a CSV file and returns a list of provinces.

    Parameters:
    - file_path (str): The path to the CSV file. Default is "src/data/province.csv".

    Returns:
    - list: A list of province names.
    """
    with open(file_path, "r") as csv_file:
        provinces = csv_file.readline().strip().split(",")

    return provinces

def provinces_cutter(provinces, provinces_count):
    """
    Randomly selects provinces from a given list.

    Parameters:
    - provinces (list): A list of province names.
    - provinces_count (int): The number of provinces to randomly select.

    Returns:
    - list: A list of randomly selected provinces.
    """
    random_provinces = random.choices(provinces, k=provinces_count)
    return random_provinces

def randomizer():
    """
    Generates a random number with specific distribution characteristics.

    Returns:
    - int: A randomly generated number with distribution characteristics.
    """
    changer = random.randint(0, 11)
    result = 0

    if changer == 0:
        result = -2
    elif changer < 3:
        result = -1
    elif changer < 8:
        result = 0
    elif changer < 10:
        result = 1
    else:
        result = 2

    return result

def trip_generator(province_set, merchandise, start_province, n_obj):
    """
    Generates a trip with random properties.

    Parameters:
    - province_set (list): List of available provinces.
    - merchandise (list): List of available merchandise.
    - start_province (str): Starting province for the trip.
    - n_obj (int): Number of objects for the trip.

    Returns:
    - dict: A dictionary representing the generated trip.
    """
    end_province = random.choice([p for p in province_set if p != start_province])

    selected_merch = random.sample(merchandise, min(n_obj, len(merchandise)))
    selected_merch_values = {merch: random.randint(1, 10) for merch in selected_merch}

    trip = {
        "from": start_province,
        "to": end_province,
        "merchandise": selected_merch_values
    }

    return trip

def merchandise_generator(tot_merch):
    """
    Generates a list of random merchandise names.

    Parameters:
    - tot_merch (int): Total number of merchandise to generate.

    Returns:
    - list: A list of randomly generated merchandise names.
    """
    merchandise = [''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 9))) for _ in range(tot_merch)]
    return merchandise

def drivers_generator(n_drivers: int) -> list[str]:
    driver_names = []
    for _ in range(n_drivers):
        driver_name = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if driver_name in driver_names: 
            driver_name = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        driver_names.append(driver_name)
    return driver_names

def single_sr_generator(province_set, merchandise, n_obj, n_trip):
    """
    Generates a list of trips (standard_route) with random starting province.

    Parameters:
    - province_set (list): List of available provinces.
    - merchandise (list): List of available merchandise.
    - n_obj (int): Number of objects for each trip.
    - n_trip (int): Number of trips to generate.

    Returns:
    - list: A list of generated trips.
    """
    start_province = random.choice(province_set)
    standard_route = []

    for _ in range(n_trip):
        trip = trip_generator(province_set, merchandise, start_province, n_obj + randomizer())
        standard_route.append(trip)
        start_province = trip["to"]

    return standard_route
 

def standard_routes_generator(sr_count, provinces_count, n_obj, merchandise, n_trip):
    """
    Generates a list of standard routes with random properties.

    Parameters:
    - sr_count (int): Number of standard routes to generate.
    - provinces_count (int): Number of provinces to randomly select.
    - n_obj (int): Number of objects for each trip.
    - merchandise (list): List of available merchandise.
    - n_trip (int): Number of trips for each standard route.

    Returns:
    - list: A list of dictionaries representing standard routes.
    """
    provinces = provinces_reader()
    random_provinces = provinces_cutter(provinces, provinces_count)

    standard_routes = []
    for i in range(sr_count):
        standard_route = {}
        standard_route["id"] = "s" + str(i+1)
        standard_route["route"] = single_sr_generator(random_provinces, merchandise, n_obj, n_trip + randomizer())
        standard_routes.append(standard_route)
    
    return standard_routes

def n_merchandise_randomizer(merch):
    """
    Randomly modifies merchandise quantities.

    Parameters:
    - merch (dict): A dictionary representing merchandise quantities.

    Returns:
    - dict: Modified merchandise dictionary.
    """
    for obj in merch.keys():
        merch[obj] = max(merch[obj] + randomizer() + randomizer(), 1)

    return merch

def t_merchandise_randomizer(merch, merchandise):
    """
    Randomly modifies merchandise items and quantities.

    Parameters:
    - merch (dict): A dictionary representing merchandise items and quantities.
    - merchandise (list): List of available merchandise.

    Returns:
    - dict: Modified merchandise dictionary.
    """
    MAX_TRIES = 5
    i = 0
    random_output = randomizer()

    if random_output > 0:
        new_merch_ind = random.choice(merchandise)
        while new_merch_ind in merch.keys() and i < MAX_TRIES:
            new_merch_ind = random.choice(merchandise)
            i = i + 1
        if i == MAX_TRIES:
            return
        merch[new_merch_ind] = random.randint(1, 10)
        i = 0
    if random_output > 1:
        new_merch_ind = random.choice(merchandise)
        while new_merch_ind in merch.keys() and i < MAX_TRIES:
            new_merch_ind = random.choice(merchandise)
            i = i + 1
        if i == MAX_TRIES:
            return
        merch[new_merch_ind] = random.randint(1, 10)
    if random_output < 0 and len(merch) > 0:
        merch.popitem()
    if random_output < -1 and len(merch) > 0:
        merch.popitem()

    return merch


def single_ar_generator(sr, province_set, merchandise):
    """
    Generate a modified actual route based on a standard route.

    Parameters:
    - sr (list): A list representing a standard route.
    - province_set (list): List of available provinces.
    - merchandise (list): List of available merchandise.

    Returns:
    - list: A list representing the modified actual route.
    """
    # Generate a random choice for each trip in sr
    trip_ind = random.choices([True, False], weights=[0.8, 0.2], k=len(sr))
    
    # Decide whether to change the starting province
    start_ind = random.choices([True, False], weights = [0.8, 0.2])

    # Create a copy of sr to avoid modifying the original list
    ar = sr.copy()

    # Lists to store 'from' and 'to' values for each step
    vec_from = [step['from'] for step in ar]
    vec_to = [step['to'] for step in ar]

    # Change the starting province if start_ind is True
    if not start_ind[0]:
        vec_from[0] = random.choice(province_set)

    # Change the ending province based on trip_ind
    for i in range(0, len(ar)):
        if not trip_ind[i]:
            vec_to[i] = random.choice(province_set)
            while vec_to[i] == vec_from[i]:
                vec_to[i] = random.choice(province_set)

    # Update 'from' values based on 'to' values
    vec_from[1:] = vec_to[:-1]

    # Update the original list
    updated_trips = []
    for i, step in enumerate(ar):
        trip = {}
        trip["from"] = vec_from[i]
        trip["to"] = vec_to[i]
        trip["merchandise"] = t_merchandise_randomizer(step["merchandise"], merchandise)
        trip["merchandise"] = n_merchandise_randomizer(step["merchandise"])
        updated_trips.append(trip)

    # Generate random values for decision-making
    n_obj = max(len(ar[random.randint(0, len(ar) - 1)]["merchandise"]) + randomizer(), 1)

    # Add a new trip if the condition is met
    if randomizer() > 1:
        start_province = random.choice(province_set)
        while start_province == updated_trips[1]["to"]:
            start_province = random.choice(province_set)
        first_trip = trip_generator(province_set, merchandise, start_province, n_obj)
        updated_trips.insert(0, first_trip)
        updated_trips[1]["from"] = updated_trips[0]["to"]

    return updated_trips


def is_subset(vector1, vector2):
    """
    Check if vector1 is a subset of vector2.

    Parameters:
    - vector1 (list): The first vector.
    - vector2 (list): The second vector.

    Returns:
    - bool: True if vector1 is a subset of vector2, False otherwise.
    """
    return all(elem in vector2 for elem in vector1)

def actual_routes_generator(standard_routes, merchandise, driver_names, n_route_4d):
    """
    Generate actual routes based on standard routes.

    Parameters:
    - standard_routes (list): A list of standard routes.
    - merchandise (list): List of available merchandise.
    - n_drivers (int): Number of drivers.
    - n_route_4d (int): Number of routes per driver.

    Returns:
    - list: A list of dictionaries representing actual routes.
    """
    province_set = provinces_reader()
    actual_routes = []

    ac_id = 1

    for driver in driver_names:
        nr = n_route_4d + randomizer()
        for r in range(nr):
            actual_route = {}
            sroute = random.choice(standard_routes)
            ar = single_ar_generator(sroute["route"], province_set, merchandise)
            actual_route["id"] = "a" + str(ac_id)
            actual_route["driver"] = driver
            actual_route["sroute"] = sroute["id"]
            actual_route["route"] = ar
            ac_id = ac_id + 1
            actual_routes.append(actual_route)

    # check if there are every sr in ar
    if not is_subset([d["sroute"] for d in actual_routes], [d["id"] for d in standard_routes]):
        id_missing = set([d["id"] for d in standard_routes]) - set([d["sroute"] for d in actual_routes])
        for code in id_missing:
            driver = random.choice(driver_names)
            actual_route = {}
            sroute = next((d for d in standard_routes if d.get("id") == code), None)
            if sroute is None:
                continue
            ar = single_ar_generator(sroute["route"], province_set, merchandise)
            actual_route["id"] = "a" + str(ac_id)
            actual_route["driver"] = driver
            actual_route["sroute"] = sroute["id"]
            actual_route["route"] = ar
            ac_id = ac_id + 1
            actual_routes.append(actual_route)

    return actual_routes



# ------------------ #
# REAL DATA GENERATION
# ------------------ #

def data_generation():
    # number of standard routes generated
    sr_count = int(os.environ.get("STANDARD_ROUTES_COUNT", 1))
    # number of trips per route
    trips_per_route = int(os.environ.get("TRIPS_PER_ROUTE", 5))
    # number of provinces to choose for the routes
    provinces_count = int(os.environ.get("PROVINCES_TO_PICK", 10))
    # extimated value of number of items per trip
    n_merchandise = int(os.environ.get("NUMBER_OF_ITEMS_PER_TRIP", 3))
    # total number of different items 
    tot_merchandise = int(os.environ.get("TOTAL_NUMBER_OF_ITEMS", 10))
    # number of routes for each driver
    drivers_count = int(os.environ.get("DRIVERS_COUNT", 10))
    # number of routes for each driver
    routes_per_driver = int(os.environ.get("ROUTES_PER_DRIVER", 15))


    # generation of merchandise
    merchandise = merchandise_generator(tot_merchandise)

    # generation of standard routes
    standard_routes = standard_routes_generator(sr_count, provinces_count, n_merchandise,
                                                merchandise, trips_per_route)

    # write standard routes on a json file
    json_writer(standard_routes, get_sr_path())

    # generation of drivers
    drivers = drivers_generator(drivers_count)

    # 2. randomize standard routes to get actual routes
    actual_routes = actual_routes_generator(standard_routes, merchandise, drivers,
                                            routes_per_driver)

    # write actual routes on a json file
    json_writer(actual_routes, get_ar_path())
