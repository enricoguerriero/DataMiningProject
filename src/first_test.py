

# imports for functions 
from utils.functions import get_actual_routes, save_run_parameters, get_standard_routes, get_coordinates_path
from utils.route_generator import data_generation
from entities.coordinate_system import CoordinateSystem
from entities.standard_route import StandardRoute
from entities.actual_route import ActualRoute

# imports libraries
import time
import random
import numpy as np

# functions:



def recommended_standard_route_generator_check(actual_routes: list[ActualRoute],
                                         standard_routes: list[StandardRoute]) -> list[StandardRoute]:
    '''
    Function for output 1:
    generates a set of recommended standard route wrote in a json file (no output)
    recommended standard route are based only on actual route
    '''

    actual_routes_train = random.sample(actual_routes, round(len(actual_routes)*0.8))
    actual_routes_test = [actual_route for actual_route in actual_routes if actual_route not in actual_routes_train]

    # pyspark session:
    import findspark
    from pyspark.sql import SparkSession
    findspark.init()
    spark = SparkSession.builder.master("local").appName(name="PySpark for clustering").getOrCreate()

    # import functions
    from first_point import create_space, build_centers, normalize_cluster_centers, \
        build_result, parameters_extraction, create_clusters, read_coordinates

    parameters = parameters_extraction(standard_routes=standard_routes)

    # creation of the space with train actual routes
    space = create_space(actual_routes=actual_routes)

    # writing coordinates of every train actual routes (according to the space) on a .csv file
    write_coordinates(actual_routes=actual_routes_train, space=space)

    # creation of a k-means clustering model
    model = create_clusters(actual_routes=actual_routes_train, n_standard_route=parameters["n_standard_route"], space=space,
                            spark=spark)

    # find centers of the model
    centers = build_centers(model=model, space=space)

    # normalize centers
    norm_centers = normalize_cluster_centers(cluster_centers=centers, actual_routes=actual_routes_train, model=model,
                                             space=space, spark=spark)

    # convert normalized centers in recommended standard route
    recommended_standard_route = build_result(normalized_centers=norm_centers, actual_routes=actual_routes_train,
                                              model=model, spark=spark)
        
    rec_sr = []
    for rsr in recommended_standard_route:
        rec_sr.append(StandardRoute(rsr))

    #writing data for rsr
    write_coordinates(actual_routes = rec_sr, space = space)

    # reading data for rsr
    rec_as_point = read_coordinates(spark)

    # writing data of original standard route
    write_coordinates(actual_routes = standard_routes, space = space)

    # reading data for standard route
    sr_data = read_coordinates(spark)

    # writing coordinates of test acutal routes
    write_coordinates(actual_routes=actual_routes_test, space=space)

    # index calculator
    index_calculator(model, spark)

    # compute the distance between test set and rec_sr
    dist = distance_from_centers(cluster_centers = centers, spark = spark)

    # compute the distance between test set and sr
    dist_origin = distance_from_sr(standard_routes = sr_data, spark = spark)

    print("\n\n -------- \n RESULTS: \n -------- \n")

    ratio = [0] * len(dist)
    for i, dist in enumerate(dist):
        if dist == 0:
            # print("There is a perfect recommended standard route")
            ratio[i] = None
        else:
            ratio[i] = dist_origin[i]/dist 
            # print(ratio[i])
    
    ratio = np.array([r for r in ratio if r])
    mean_ratio = np.exp(np.mean(np.log(ratio)))
    print("Mean of ratios: ", mean_ratio)
    pss = np.count_nonzero(ratio == 0)
    # print("Perfect Standard Route executed: ", pss)
    ratio_diff_from_zero = ratio[ratio != 0]
    mean_ratio_d = np.exp(np.mean(np.log(ratio_diff_from_zero)))
    print("Mean of ratio except perfect standard route: ", mean_ratio_d)
    

    spark.stop()


def index_calculator(model, spark):
    from pyspark.ml.evaluation import ClusteringEvaluator
    from first_point import read_coordinates

    test_data = read_coordinates(spark)

    predictions = model.transform(test_data)
    # Evaluate clustering by computing Silhouette score
    evaluator = ClusteringEvaluator()

    silhouette = evaluator.evaluate(predictions)
    # value close to 1 means that the clustering is good
    print("Silhouette with squared euclidean distance = " + str(silhouette))

    # Calculate Davies-Bouldin Index using sklearn
    from sklearn.metrics import davies_bouldin_score

    # Convert the PySpark DataFrame to a Pandas DataFrame
    predictions_pandas = predictions.select("prediction").toPandas()

    # Calculate Davies-Bouldin Index
    davies_bouldin = davies_bouldin_score(predictions_pandas.values, predictions_pandas["prediction"].values)
    print(f"Davies-Bouldin Index: {davies_bouldin}")

    # Calculate Calinski-Harabasz Index using sklearn
    from sklearn.metrics import calinski_harabasz_score

    # Convert the PySpark DataFrame to a Pandas DataFrame
    predictions_pandas = predictions.select("prediction").toPandas()

    # Convert features to NumPy array
    features_array = np.array(predictions.select("features").rdd.map(lambda row: row.features.toArray()).collect())
    
    # Convert features_array to a 2D NumPy array
    features_array_2d = np.array(features_array)

    # Calculate Calinski-Harabasz Index
    calinski_harabasz = calinski_harabasz_score(features_array_2d, predictions_pandas["prediction"].values)
    print(f"Calinski-Harabasz Index: {calinski_harabasz}")


import math
def distance_from_rec_sr(cluster_centers, spark):
    from first_point import read_coordinates
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.linalg import DenseVector
    import numpy as np

    data = read_coordinates(spark)

    df = cluster_centers.select("id", "features")

    feature_cols = data.columns[1:]
    vect_assembler = VectorAssembler(inputCols=feature_cols, outputCol="data_features")
    data = vect_assembler.transform(data)   
    data = data.select("id", "data_features")

    dist = []
    for point in data.select("data_features").collect():
        min_dist = -1
        for center in df.select("features").collect():
            dense_center = DenseVector(center)
            dense_point = DenseVector(point)
            a_center = np.array(dense_center)[0]
            a_point = np.array(dense_point)[0][:math.floor(len(data.select("data_features").collect()[0][0])/2)]
            if min_dist == -1:
                min_dist = euclidean_distance_udf(a_center, a_point)
            else:
                min_dist = min(min_dist, euclidean_distance_udf(a_center, a_point))
        dist.append(min_dist)
    return(dist)


def distance_from_centers(cluster_centers, spark):
    from first_point import read_coordinates
    from pyspark.sql.types import StructType, StructField, FloatType
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.linalg import DenseVector
    import numpy as np

    data = read_coordinates(spark)
    
    field_names = cluster_centers[0].keys()
    schema = StructType([StructField(field, FloatType(), True) for field in field_names])
    cluster_centers = spark.createDataFrame([{field: float(value) if isinstance(value, (int, float)) else value for field, value in d.items()} for d in cluster_centers], schema=schema)
    
    feature_cols = cluster_centers.columns[1:]
    vec_assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    df = vec_assembler.transform(cluster_centers)   
    df = df.select("pred", "features")

    feature_cols = data.columns[1:]
    vect_assembler = VectorAssembler(inputCols=feature_cols, outputCol="data_features")
    data = vect_assembler.transform(data)   
    data = data.select("id", "data_features")

    dist = []
    for point in data.select("data_features").collect():
        min_dist = -1
        for center in df.select("features").collect():
            dense_center = DenseVector(center)
            dense_point = DenseVector(point)
            a_center = np.array(dense_center)[0]
            a_point = np.array(dense_point)[0][:math.floor(len(data.select("data_features").collect()[0][0])/2)]
            if min_dist == -1:
                min_dist = euclidean_distance_udf(a_center, a_point)
            else:
                min_dist = min(min_dist, euclidean_distance_udf(a_center, a_point))
        dist.append(min_dist)
    return(dist)



def distance_from_sr(standard_routes, spark):
    from first_point import read_coordinates
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.linalg import DenseVector
    import numpy as np

    data = read_coordinates(spark)
    df = standard_routes
    
    feature_cols = data.columns[1:]
    vect_assembler = VectorAssembler(inputCols=feature_cols, outputCol="data_features")
    data = vect_assembler.transform(data)   
    data = data.select("id", "data_features")
    
    dist = []
    for point in data.select("data_features").collect():
        min_dist = None
        for center in df.select("features").collect():
            dense_center = DenseVector(center)
            dense_point = DenseVector(point)
            a_center = np.array(dense_center)[0]
            a_point = np.array(dense_point)[0][:math.floor(len(data.select("data_features").collect()[0][0])/2)]
            if not min_dist:
                min_dist = euclidean_distance_udf(a_center, a_point)
            else:
                min_dist = min(min_dist, euclidean_distance_udf(a_center, a_point))
        dist.append(min_dist)
    return(dist)




def euclidean_distance_udf(point, fixed_point):
    import numpy as np
    return np.sqrt(np.sum((point - fixed_point) ** 2))


import csv
def write_coordinates(actual_routes: list[StandardRoute], space: CoordinateSystem):
    header: list[str] = []
    header.append("id")
    header.extend(space.all_city_vec)
    header.extend(space.all_merch)
    header.extend(space.all_trip)

    with open(get_coordinates_path(), "w") as f:
        writer = csv.writer(f)

        # Write the header
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


standard_routes = get_standard_routes()
actual_routes = get_actual_routes()


# Test cluster for first point

start = int(round(time.time() * 1000))
rec_standard_routes = recommended_standard_route_generator_check(actual_routes = actual_routes, standard_routes = standard_routes)
end = int(round(time.time() * 1000))
print(f"recommended standard routes generated in {end - start} milliseconds\n")


