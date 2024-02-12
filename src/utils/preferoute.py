from entities.standard_route import StandardRoute
from entities.preferences import Preferences


def preferoute_similarity(route: StandardRoute, prefe: Preferences, weights: list = [1]*10) -> float:
    '''
    calculate a sort of similarity between a Standard (or Actual, as child class) route and a preference of a driver
    can choose a weight vector, default all one
    auto standardized weight
    '''

    # evaluation point by point
    sim = []

    # 1. city frequency
    sim.insert(0, 0)
    den = sum(prefe.freq_city[city] for city in prefe.freq_city.keys())
    for city in route.extract_city():
        if city in prefe.freq_city.keys():
            val = prefe.freq_city[city] / den
            sim[0] += val

    # 2. start frequency
    sim.insert(1, 0)
    if route.extract_city()[0] in prefe.freq_start.keys():
        sim[1] = 1
        

    # 3. finish frequency
    sim.insert(2, 0)
    if route.extract_city()[-1] in prefe.freq_finish.keys():
        sim[2] = 1

    # 4. trip frequency
    sim.insert(3, 0)
    den = sum(prefe.freq_trip[trip] for trip in prefe.freq_trip.keys())
    for trip in route.trip_without_merch():
        if trip in prefe.freq_trip.keys():
            val = prefe.freq_trip[trip] / den
            sim[3] += val

    # 5. city frequent itemset
    sim.insert(4, 0)
    den = sum(prefe.freq_itemset_city[key] for key in prefe.freq_itemset_city.keys())
    for city_combo in generate_2_tuples(route.extract_city()):
        if city_combo in prefe.freq_itemset_city.keys():
            val = prefe.freq_itemset_city[city_combo] / den
            sim[4] += val

    # 6. trip frequent itemset
    sim.insert(5, 0)
    den = sum(prefe.freq_itemset_trip[key] for key in prefe.freq_itemset_trip.keys())
    for trip_combo in generate_2_tuples(route.trip_without_merch()):
        if trip_combo in prefe.freq_itemset_trip.keys():
            val = prefe.freq_itemset_trip[trip_combo] / den
            sim[5] += val

    # 7. avg n trip
    sim.insert(6, max(1 - 2*(abs(len(route.route) - prefe.n_trip)/(len(route.route) + prefe.n_trip)), 0))

    # 8. avg n merch items
    avg_merch_n = 0
    for trip in route.route:
        avg_merch_n += len(trip.merchandise.item)
    avg_merch_n = avg_merch_n/len(route.route)
    sim.insert(7, max(1 - 2*(abs(avg_merch_n - prefe.type_merch_avg)/(avg_merch_n + prefe.type_merch_avg)), 0))

    # 9. merch frequency
    sim.insert(8, 0)
    den = sum(prefe.n_merch.values())
    for merch in route.extract_merch().item:
        if merch in prefe.n_merch:
            val = prefe.n_merch[merch] / den
            sim[8] += val

    # 10. avg total merch per trip
    avg_merch_quantity = 0
    for quantity_merch in route.extract_merch().quantity:
        avg_merch_quantity += quantity_merch
    avg_merch_quantity = avg_merch_quantity / len(route.extract_merch().quantity)
    sim.insert(9, max(1 - (abs(avg_merch_quantity - prefe.n_merch_per_route) / (avg_merch_quantity + prefe.n_merch_per_route)), 0))

    # 11. merch frequent itemset per trip
    #sim[10] = 0

        
    # return weighted mean (after standardizing weights)
    total_weight = sum(weights)
    standardized_weights = []
    for weight in weights:
        standardized_weights.append(weight/total_weight)
    
    similarity = 0
    for i in range(len(sim)):
        similarity += sim[i] * standardized_weights[i]

    return similarity


def generate_2_tuples(input_vector):
    from itertools import combinations
    # Use combinations to generate all 2-tuples
    result = list(combinations(input_vector, 2))
    return result
