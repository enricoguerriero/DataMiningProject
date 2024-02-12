# functions for the first output


# imports:

import csv
import os
import numpy as np

from dotenv import load_dotenv

from entities.standard_route import StandardRoute
from entities.actual_route import ActualRoute
from entities.coordinate_system import CoordinateSystem

from pyspark.ml.clustering import KMeans, KMeansModel

from utils.functions import get_coordinates_path


# loading environment

load_dotenv()

run_id = os.environ.get("RUN_ID", "1")


# functions:

def parameters_extraction(standard_routes: list[StandardRoute]) -> dict:
    """
    extraction of:
    - n_standard_route
    - trip_per_route
    - merch_per_trip
    """
    parameters = {}
    parameters["n_standard_route"] = len(standard_routes)
    trip_counter = 0
    merch_counter = 0
    for sr in standard_routes:
        trip_counter += len(sr.route)
        merch_counter_prov = 0
        for trip in sr.route:
            merch_counter_prov += len(trip.merchandise.item)
            merch_counter += merch_counter_prov / len(trip.city_from)
    parameters["trips_per_route"] = round(trip_counter / len(standard_routes))
    parameters["merch_per_trip"] = round(merch_counter / len(standard_routes))
    return parameters


def create_space(actual_routes: list[ActualRoute]) -> CoordinateSystem:
    city_list = []
    merch_list = []
    trip_list = []
    for actual_route in actual_routes:
        cities = actual_route.extract_city()
        cities = list(dict.fromkeys(cities))
        city_list += [city for city in cities if city not in city_list]
        merch_vec = actual_route.extract_merch().item
        merch_vec = list(dict.fromkeys(merch_vec))
        merch_list += [merch for merch in merch_vec if merch not in merch_list]
        trips = actual_route.trip_string()
        trips = list(dict.fromkeys(trips))
        trip_list += [trip for trip in trips if trip not in trip_list]

    return CoordinateSystem(city_list, merch_list, trip_list)


def write_coordinates(actual_routes: list[ActualRoute], space: CoordinateSystem):
    header: list[str] = []
    header.append("id")
    header.extend(space.all_city_vec)
    header.extend(space.all_merch)
    header.extend(space.all_trip)

    with open(get_coordinates_path(), "w") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for ar in actual_routes:
            row_result = []
            row_result.append(ar.id)
            actual_route_cities = ar.extract_city()
            for city in space.all_city_vec:
                row_result.append(5 if city in actual_route_cities else 0)
            actual_route_merch = ar.extract_merch()
            total_quant = sum(actual_route_merch.quantity)
            for merch in space.all_merch:
                if merch in actual_route_merch.item:
                    index = actual_route_merch.item.index(merch)
                    row_result.append(actual_route_merch.quantity[index] / total_quant)
                else:
                    row_result.append(0)
            actual_route_trips = ar.trip_string()
            for trip in space.all_trip:
                row_result.append(10 if trip in actual_route_trips else 0)
            writer.writerow(row_result)
    f.close()


def read_coordinates(spark):
    from pyspark.ml.feature import VectorAssembler
    from pyspark.sql.functions import monotonically_increasing_id

    data = spark.read.option("header", True) \
        .option("inferSchema", True) \
        .csv(get_coordinates_path())

    input_cols = data.columns[1:]
    vec_assembler = VectorAssembler(inputCols = input_cols, outputCol = "features")
    final_data = vec_assembler.transform(data)
    final_data = final_data.withColumn("index", monotonically_increasing_id())

    return(final_data)


def create_clusters(actual_routes:list[ActualRoute], n_standard_route: int, space: CoordinateSystem, spark) -> KMeansModel:

    write_coordinates(actual_routes = actual_routes, space = space)

    data = read_coordinates(spark)

    kmeans = KMeans() \
        .setK(n_standard_route) \
        .setSeed(1) \
        .setFeaturesCol("features") 
    model = kmeans.fit(data)

    return model


def build_centers(model: KMeansModel, space: CoordinateSystem) -> list:

    cluster_centers = []
    centers = model.clusterCenters()
    for i, center in enumerate(centers):
        cluster_center = {}
        cluster_center["pred"] = i
        for index, key in enumerate(space.all_city_vec + space.all_merch + space.all_trip):
            cluster_center[key] = center[index]
        cluster_centers.append(cluster_center)

    return(cluster_centers)

def normalize_cluster_centers(cluster_centers: list, actual_routes: list[ActualRoute], model, space: CoordinateSystem, spark) -> list:
    from pyspark.sql.functions import col

    data = read_coordinates(spark)
    
    normalized_centers = []
    for index, center in enumerate(cluster_centers):
        normalized_center = {}
        normalized_center["pred"] = center["pred"]

        predictions = model.transform(data)
        indexed_data = predictions.select("index", "prediction")
        target_cluster = index
        cluster_indexes = (
            indexed_data
            .filter(col("prediction") == target_cluster)
            .select("index")
            .orderBy("index")
        )
        indexes_list = [row["index"] for row in cluster_indexes.collect()]

        small_ar_set = []
        for i, ar in enumerate(actual_routes):
            if i in indexes_list:
                small_ar_set.append(ar)
        
        parameters = parameters_extraction(small_ar_set)
        trips_per_route = parameters["trips_per_route"]
        merch_per_trip = parameters["merch_per_trip"]
        
        cities_values = []
        trips_values = []
        merch_values = []
        for key in center.keys():
            value = center[key]
            if key in space.all_city_vec and value > 0:
                # ignore if the value is 0
                cities_values.append(value)
            elif key in space.all_trip and value > 0:
                trips_values.append(value)
            elif value > 0:
                # merch case
                merch_values.append(center[key])

        cities_values.sort(reverse = True)
        threshold_index_cities = trips_per_route + 1
        threshold_index_cities = min(threshold_index_cities, len(cities_values))
        threshold_cities = cities_values[threshold_index_cities - 1]
        city_vec = []
        counter = 0
        for key in space.all_city_vec:
            if center[key] >= threshold_cities and counter <= trips_per_route:
                city_vec.append(key)
                counter += 1

        trips_values.sort(reverse = True)
        threshold_index_trips = trips_per_route 
        threshold_index_trips = min(threshold_index_trips, len(trips_values))
        threshold_trips = trips_values[threshold_index_trips - 1]
        trip_vec = []
        counter = 0
        for key in space.all_trip:
            if center[key] >= threshold_trips and counter < trips_per_route:
                trip_vec.append(key)
                counter += 1

        merch_values.sort(reverse = True)
        threshold_index_merch = trips_per_route * merch_per_trip
        threshold_index_merch = min(threshold_index_merch, len(merch_values))
        threshold_merch = merch_values[threshold_index_merch - 1]
        merch_vec = []
        for key in space.all_merch:
            if center[key] >= threshold_merch:
                merch_vec.append(key)

        normalized_center["trip"] = trip_vec
        normalized_center["city"] = city_vec
        normalized_center["merch"] = merch_vec
        normalized_centers.append(normalized_center)

    return normalized_centers


def build_result(normalized_centers: list, actual_routes: list[ActualRoute], model: KMeansModel, spark):
    from pyspark.sql.functions import col

    rec_routes = []
    data = read_coordinates(spark)

    for index, center in enumerate(normalized_centers):
        rsr = {"id": 's' + str(center["pred"] + 1)}
        route = []
        
        i = 0
        chain = []
        while len(chain) < 2 and i < len(center["trip"]):
            found = True
            chain = [center["trip"][i]]
            while found:
                found = False
                for trip in center["trip"]:
                    if trip not in chain:
                        city_from, city_to = trip.split(":")
                        ch_city_to = chain[-1].split(":")[1]
                        ch_city_from = chain[0].split(":")[0]
                        if city_from == ch_city_to:
                            found = True
                            chain = chain + [trip]
                        elif city_to == ch_city_from:
                            found = True
                            chain = [trip] + chain
            i += 1

        if len(chain) == 1:
            city_chain = center["city"]
        else:
            city_chain = [chain[0].split(":")[0]]
            for trip in chain:
                city_chain.append(trip.split(":")[1])
            city_chain.extend(city for city in center["city"] if city not in city_chain)
            if len(city_chain) > len(center["city"]):
                city_chain = city_chain[:len(center["city"])]
        
        city_from_vec = []
        city_to_vec = []

        predictions = model.transform(data)
        indexed_data = predictions.select("index", "prediction")
        target_cluster = index
        cluster_indexes = (
            indexed_data
            .filter(col("prediction") == target_cluster)
            .select("index")
            .orderBy("index")
        )
        indexes_list = [row["index"] for row in cluster_indexes.collect()]
        
        small_ar_set = []
        for i, ar in enumerate(actual_routes):
            if i in indexes_list:
                small_ar_set.append(ar)
        for i, city in enumerate(city_chain):
            if i != len(city_chain)-1:
                city_from_vec.append(city)
            if i == 0:
                continue
            city_to_vec.append(city)
        small_space = create_space(small_ar_set)
        parameters = parameters_extraction(small_ar_set)
        freq_merch = merch_per_city_counter(small_ar_set, small_space, t_hold_n = parameters["merch_per_trip"])
        for i, city in enumerate(city_to_vec):
            merch_vec_item = []
            merch_vec_quantity = []
            for merch_item in freq_merch[city].keys():
                if freq_merch[city][merch_item][1] != 0:
                    merch_vec_item.append(merch_item)
                    merch_vec_quantity.append(freq_merch[city][merch_item][1])
            merch = dict(zip(merch_vec_item, merch_vec_quantity))
            trip = {"from": city_from_vec[i], "to": city, "merchandise": merch}
            route.append(trip)

        rsr["route"] = route
        rec_routes.append(rsr)
    return rec_routes
            

def merch_per_city_counter(actual_routes: list[ActualRoute], space: CoordinateSystem, t_hold_n: int = None, t_hold_q: int = None) \
        -> dict[str, dict[str, list[int, int]]]:

    result = {}

    for city in space.all_city_vec:
        counter = {merch: [0, 0] for ar in actual_routes for merch in ar.extract_merch().item}
        for ar in actual_routes:
            for trip in ar.route:
                if trip.city_to == city:
                    for i, merch_key in enumerate(trip.merchandise.item):
                        counter[merch_key][0] += 1
                        counter[merch_key][1] += trip.merchandise.quantity[i]
        for merch_key, (count, quantity) in counter.items():
            if count > 0:
                counter[merch_key][1] = round(quantity / count)
        if t_hold_n:
            counter = dict(sorted(counter.items(), key=lambda x: x[1][0], reverse=True)[:t_hold_n])        
        elif t_hold_q:
            counts = [count for _, (count, _) in counter.items()]
            threshold_value = np.percentile(counts, t_hold_q)
            counter = {merch: [count, quantity] for merch, (count, quantity) in counter.items() if count >= threshold_value}
        result[city] = counter

    return result
