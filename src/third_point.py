from entities.preferences import Preferences
from entities.actual_route import ActualRoute
from entities.trip import Trip
from utils.functions_pref import get_actual_routes_per_driver, extract_drivers
from utils.functions import get_actual_routes
from itertools import chain
from operator import xor
import random
from utils.functions import json_writer, get_third_output_path
import copy


def generate_path(pref: Preferences) -> list[tuple]:
    # if there are trips that have common ends we give priority to them
    new_freq_itemset = {}

    if round(pref.n_trip) <= 0:
        raise ValueError("Average number of trips per route below one, remove routes with 0 trips.")

    if round(pref.n_trip) == 1:
        result_one = []
        for item in pref.freq_trip:
            result_one.append(item)
            break
        return result_one

    for (trip_couple, value) in pref.freq_itemset_trip.items():
        # if the trips are already combined
        if trip_couple[0][1] == trip_couple[1][0]:
            new_freq_itemset[trip_couple] = value
        elif trip_couple[0][0] == trip_couple[1][1]:
            new_freq_itemset[(trip_couple[1], trip_couple[0])] = value

    # if we didn't find anything, we concatenate them
    if not new_freq_itemset and round(pref.n_trip) > 2:
        for (trip_couple, value) in pref.freq_itemset_trip.items():
            # we add the third trip in the middle
            new_trip_set = (trip_couple[0], (trip_couple[0][1], trip_couple[1][0]), trip_couple[1])
            new_freq_itemset[new_trip_set] = value

    if not new_freq_itemset and round(pref.n_trip) == 2:
        eligible_cities_small = [list(chain.from_iterable(trip_couple)) for trip_couple in pref.freq_itemset_trip]
        small_freq_itemset_return = (eligible_cities_small[0][0], eligible_cities_small[0][1])
        small_result = [small_freq_itemset_return]

        for item in pref.freq_trip:
            if small_freq_itemset_return[0] == item[-1] and item != small_freq_itemset_return:
                small_result.insert(0, item)
                break

            elif small_freq_itemset_return[1] == item[0] and item != small_freq_itemset_return:
                small_result.append(item)
                break

        # frequent start
        if len(small_result) == 1:
            for item in pref.freq_start:
                if item not in small_freq_itemset_return:
                    small_result.insert(0, (item, small_freq_itemset_return[0]))
                    break
                elif item == small_freq_itemset_return[0]:
                    break

        # frequent finish
        if len(small_result) == 1:
            for item in pref.freq_start:
                if item not in small_freq_itemset_return:
                    small_result.append((small_freq_itemset_return[1], item))
                    break

        return small_result

    eligible_cities = [list(chain.from_iterable(trip_couple)) for trip_couple in new_freq_itemset]

    result = []
    for i in range(0, len(eligible_cities)):
        result_prov = eligible_cities[i]
        for j in range(i+1, len(eligible_cities)):
            if (result_prov[0] == eligible_cities[j][-1] and (len(result_prov) + len(eligible_cities[j]))
                    < (round(pref.n_trip) * 2) - 1):
                result_prov[:0] = eligible_cities[j]

            elif (result_prov[-1] == eligible_cities[j][0] and (len(result_prov) + len(eligible_cities[j]))
                  < (round(pref.n_trip) * 2) - 1):
                result_prov.extend(eligible_cities[j])
        result.append(result_prov)

    freq_itemset_result_str = max(result, key=lambda x: (len(x)))
    freq_itemset_result = [(freq_itemset_result_str[i], freq_itemset_result_str[i + 1])
                           for i in range(0, len(freq_itemset_result_str), 2)]

    # we finished frequent itemset, now we delve into frequent trips
    if len(freq_itemset_result) >= round(pref.n_trip):
        return freq_itemset_result

    result = freq_itemset_result_str

    i = 1
    while i == 1:
        i = 0
        for item in pref.freq_trip:
            if (result[0] == item[-1] and len(result) < (round(pref.n_trip) * 2) - 1
                    and item not in freq_itemset_result):  # update itemset
                result[:0] = item
                freq_itemset_result.append(item)
                i = 1
                break

            elif result[-1] == item[0] and len(result) < (round(pref.n_trip) * 2) - 1 \
                    and item not in freq_itemset_result:
                result.extend(item)
                freq_itemset_result.append(item)
                i = 1
                break

    freq_trip_result = [(result[i], result[i + 1]) for i in range(0, len(result), 2)]

    if len(freq_trip_result) >= round(pref.n_trip):
        return freq_trip_result

    # frequent trips is now alright, let's look at frequent starts and finish
    dummy_start = 0

    for item in pref.freq_start:
        if item not in result:
            result[:0] = (item, 'PlaceholderS')
            break
        elif item == result[0]:
            dummy_start = 1
            break

    # since preferences has ceil(n_trip) records, we will surely find a starting point that isn't already in the route,
    # or at least that is the first record of the route

    if len(result) >= round(pref.n_trip) * 2:
        if 'PlaceholderS' in result:
            result[1] = result[2]
        freq_start_result = [(result[i], result[i + 1]) for i in range(0, len(result), 2)]
        return freq_start_result

    for item in pref.freq_finish:
        # if we have a new city as finish
        if item not in result:
            result.append('Placeholder')
            result.append(item)
            break

        # we only consider the last city of the set as the finish if we didn't already set the start within the set
        elif dummy_start == 0 and item == result[-1]:
            break

    if 'PlaceholderS' in result and 'Placeholder' in result:
        # if we have added a new start and a new finish from now on we add from the finish
        result[1] = result[2]

    if len(result) >= round(pref.n_trip) * 2:
        if 'Placeholder' in result:
            result[-2] = result[-3]
        freq_finish_result = [(result[i], result[i + 1]) for i in range(0, len(result), 2)]
        return freq_finish_result

    # frequent start/finish is now alright, let's do frequent itemset cities

    i = 1
    while i == 1 and len(result) < (round(pref.n_trip) * 2) - 1:
        i = 0
        for item in pref.freq_itemset_city:
            if xor(item[0] in result, item[1] in result):
                if item[0] in result and 'PlaceholderS' in result:
                    result[1] = item[1]
                    result.insert(2, item[1])
                    result.insert(3, 'PlaceholderS')
                    i = 1
                    break

                if item[0] in result and 'Placeholder' in result:
                    result[-2] = item[1]
                    result.insert(-2, 'Placeholder')
                    result.insert(-2, item[1])

                    i = 1
                    break

                if item[1] in result and 'PlaceholderS' in result:
                    result[1] = item[0]
                    result.insert(2, item[0])
                    result.insert(3, 'PlaceholderS')
                    i = 1
                    break

                if item[1] in result and 'Placeholder' in result:
                    result[-2] = item[0]
                    result.insert(-2, 'Placeholder')
                    result.insert(-2, item[0])
                    i = 1
                    break

    if len(result) >= round(pref.n_trip) * 2:
        for i, item in enumerate(result):
            if item == 'Placeholder':
                result[i] = result[i - 1]
            if item == 'PlaceholderS':
                result[i] = result[i + 1]
        freq_item_city_result = [(result[i], result[i + 1]) for i in range(0, len(result), 2)]

        return freq_item_city_result

    # frequent itemset city alright, last step

    for item in pref.freq_city:
        if item not in result and len(result) < (round(pref.n_trip) * 2) - 1:
            if 'Placeholder' in result:
                for i, city in enumerate(result):
                    if city == 'Placeholder':
                        result[i] = item
                        result.insert(i, item)
                        result.insert(i, 'Placeholder')
                        break

            if 'PlaceholderS' in result:
                for i, city in enumerate(result):
                    if city == 'PlaceholderS':
                        result[i] = item
                        result.insert(i + 1, 'PlaceholderS')
                        result.insert(i + 1, item)
                        break

    for i, item in enumerate(result):
        if item == 'Placeholder':
            result[i] = result[i - 1]
        if item == 'PlaceholderS':
            result[i] = result[i + 1]
    freq_city_result = [(result[i], result[i + 1]) for i in range(0, len(result), 2)]

    return freq_city_result


def generate_merch(trip: tuple, pref: Preferences) -> dict:
    """Attaches the merch to the trip"""

    if trip[1] in pref.n_merch_per_city:
        deep = copy.deepcopy(pref.n_merch_per_city)
        for (key, value) in deep[trip[1]].items():
            deep[trip[1]][key] = value[1]

        return deep[trip[1]]

    else:
        merch_types = random.sample(list(pref.n_merch.keys()), k=round(pref.type_merch_avg))
        mean_for_item = round(pref.n_merch_per_route/pref.type_merch_avg)
        if mean_for_item - 5 >= 0:
            return {item: random.randint(mean_for_item - 5, mean_for_item + 5) for item in merch_types}
        else:
            return {item: random.randint(0, mean_for_item + 5) for item in merch_types}


def generate_trips(trips: list[tuple], pref: Preferences) -> dict:
    driver = pref.driver
    route = []
    result = {'driver': driver, 'route': route}
    for trip in trips:
        route.append({"from": trip[0], "to": trip[1], "merchandise": generate_merch(trip, pref)})

    return result

