import random
from entities.actual_route import ActualRoute
from entities.standard_route import StandardRoute
from second_point import get_drivers_preferences, get_similarity_per_driver, get_top_five_per_driver
from utils.preferoute import preferoute_similarity
from third_point import generate_trips, generate_path
from entities.preferences import Preferences
from utils.functions import get_actual_routes, get_standard_routes
import numpy as np
import matplotlib.pyplot as plot


def get_top_five_per_driver_and_mean(similarity_per_driver: dict[str, dict[str, float]]) -> list[dict[str, str]]:
    top_five_per_driver = []
    means = {}
    for driver_name in similarity_per_driver:
        driver_similarities = similarity_per_driver[driver_name]
        sorted_sim = sorted(driver_similarities.items(), key = lambda x: x[1], reverse = True)[:5]
        other_sim = [sim[1] for sim in driver_similarities.items() if sim not in sorted_sim]
        sim_mean = sum(other_sim) / len(other_sim)
        top_five = {}
        top_five["driver"] = driver_name
        top_five["routes"] = [route[0] for route in sorted_sim]
        top_five_per_driver.append(top_five)
        means[driver_name] = sim_mean
    return top_five_per_driver, means


def ratio_sim_and_mean(top_five_per_driver, means):
    ratios = []
    for driver in top_five_per_driver:
        ratio = sum(top_five_per_driver[driver])/means[driver]
        ratios.append(ratio)
    ratios = np.array(ratios)
    mean = np.exp(np.mean(np.log(ratios)))
    return mean

def diff_sim_and_mean(top_five_per_driver, means):
    diffs = []
    for driver in top_five_per_driver:
        diff = sum(top_five_per_driver[driver])/len(top_five_per_driver[driver]) - means[driver]
        diffs.append(diff)
    diffs = np.array(diffs)
    mean = np.mean(diffs)
    return mean


def test_ideal_route_driver(preferences: Preferences, ideal: dict):

    ideal['id'] = ideal['driver']
    stand_route = StandardRoute(ideal)
    weight_list = [3, 3, 3, 10, 5, 10, 10, 1, 2, 1]

    distance = preferoute_similarity(stand_route, preferences, weight_list)

    return distance


def data_adaptation(act_route_train: list[ActualRoute], act_route_test: list[ActualRoute]):
    pref_train = get_drivers_preferences(act_route_train)
    pref_final = get_drivers_preferences(act_route_test)

    similarity_dict_train = get_similarity_per_driver(pref_train, get_standard_routes())
    similarity_dict = get_similarity_per_driver(pref_final, get_standard_routes())

    best_five = get_top_five_per_driver(similarity_dict_train)

    best_five_t, means = get_top_five_per_driver_and_mean(similarity_dict)
    sim_dict = {}

    sol_dict_2 = {}

    for dictionary in best_five_t:

        driver = dictionary["driver"]
        driver_pref = {driver: pref_final[driver]}
        driver_top_five = dictionary["routes"]
        five_standard_routes = []
        for sr in get_standard_routes():
            if sr.id in driver_top_five:
                five_standard_routes.append(sr)
        similarity_dict = get_similarity_per_driver(driver_pref, five_standard_routes)

        sol_dict_2[driver] =  np.mean(np.array(list(similarity_dict[driver].values())))

        sim_dict[driver] = similarity_dict[driver].values()

    print("Ratio between mean of 5 best standard routes and the others:", ratio_sim_and_mean(sim_dict, means))
    print("Difference between mean of 5 best standard routes and the others:", diff_sim_and_mean(sim_dict, means))

    sol_dict = {}

    for dictionary in best_five:

        driver = dictionary["driver"]
        driver_pref = {driver: pref_final[driver]}
        driver_top_five = dictionary["routes"]
        five_standard_routes = []
        for sr in get_standard_routes():
            if sr.id in driver_top_five:
                five_standard_routes.append(sr)
        similarity_dict = get_similarity_per_driver(driver_pref, five_standard_routes)

        sol_dict[driver] = np.mean(np.array(list(similarity_dict[driver].values())))



    return(sol_dict, sol_dict_2)    


def mean_variation(test_result: dict):
    means = np.array(list(test_result.values()))
    mean_value = np.mean(means)

    plot.boxplot(list(test_result.values()))
    plot.title('Boxplot of Similarity Variation')
    plot.ylabel('Values')
    plot.grid(True, linestyle='--', alpha=0.5)
    plot.xticks([])
    plot.show()

    return(mean_value)



actual_routes = get_actual_routes()

actual_routes_train = random.sample(actual_routes, round(len(actual_routes) * 0.8))

d1, d2 = data_adaptation(actual_routes_train, actual_routes)

mean_value = mean_variation(d1)

print("Mean of distance between preferences from all actual routes and standard routes selected by train set: ", mean_value)


mean_value = mean_variation(d2)

print("Mean of distance between preferences from all actual routes and standard routes selected by all actual routes: ", mean_value)
