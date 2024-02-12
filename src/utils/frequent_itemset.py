import time
import itertools


def hash_pair(n1, n2, n_buckets):
    """Generates a basic hash function starting from string or tuple"""

    # The hash function is the modulo of the sum of the total ASCII values of the parameters divided by the number of buckets
    return (hash((n1, n2)) * hash((n1[0], n2[0]))) % n_buckets


def second_hash_pair(n1, n2, n_buckets):
    """Generates a second basic hash function starting from string or tuple"""

    return (hash((n1, n2))) % n_buckets


def pcy_basket(basket: list, n_buckets: int, pairs_hashtable: dict, second_pairs_hashtable: dict, singletons: dict,
               comb):
    """Does the first pass of the PCY for a single basket, its only use is to modify its parent's dictionaries"""

    "count frequency of the items"
    for item in basket:
        singletons[item] = singletons.get(item, 0) + 1

    "creates the couples with itertools (tuple) and adds them to a dictionary with the respective count"
    for key in itertools.combinations(singletons, comb):
        "Applying hash function"
        hash_value = hash_pair(key[0], key[1], n_buckets)
        "If the hash value is present we add to its count"
        pairs_hashtable[hash_value] = pairs_hashtable.get(hash_value, 0) + 1

    for key in itertools.combinations(singletons, comb):
        "Applying hash function"
        hash_value = second_hash_pair(key[0], key[1], n_buckets)
        "If the hash value is present we add to its count"
        second_pairs_hashtable[hash_value] = second_pairs_hashtable.get(hash_value, 0) + 1


def run_pcy(baskets: list[list[str or tuple]], n_buckets: int, t_hold: float, start=time.time(), comb=2):
    frequent_pairs = {}

    while not frequent_pairs:

        singletons = {}
        pairs_count_hash = {}
        second_pairs_count_hash = {}

        for item in baskets:
            pcy_basket(item, n_buckets, pairs_count_hash, second_pairs_count_hash, singletons, comb=comb)

        "remove singletons that are not frequent"
        frequent_single_items = {}
        for key in singletons.items():
            if key[1] >= len(baskets) * t_hold:
                frequent_single_items[key[0]] = key[1]

        "creates a list containing only the names of the frequent items (remove the count)"
        frequent_singletons = [item for item in frequent_single_items]

        # BETWEEN PASSES
        bitmap = [0] * n_buckets  # bitmap that will summarise which baskets have the minimum support
        "transform into a bit vector with value 1 if the count is over the threshold"
        for key in sorted(pairs_count_hash.keys()):
            if pairs_count_hash[key] > len(baskets) * t_hold:
                bitmap[key] = 1

        bitmap2 = [0] * n_buckets  # bitmap that will summarise which baskets have the minimum support
        "transform into a bit vector with value 1 if the count is over the threshold"
        for key in sorted(second_pairs_count_hash.keys()):
            if second_pairs_count_hash[key] > len(baskets) * t_hold:
                bitmap2[key] = 1

        # PASS 2
        "we only keep the pairs that have frequent singletons and belong to a frequent bucket"
        candidate_pairs = {}
        for i in range(0, len(frequent_singletons)):
            for j in range(i + 1, len(frequent_singletons)):
                "we find out if the pair belongs to a frequent bucket"
                hash_value = hash_pair(frequent_singletons[i], frequent_singletons[j], n_buckets)
                second_hash_value = second_hash_pair(frequent_singletons[i], frequent_singletons[j], n_buckets)
                if bitmap[hash_value] > 0 and bitmap2[second_hash_value] > 0:
                    "if it belongs to a frequent bucket we consider it as a candidate"
                    candidate_pair = (frequent_singletons[i], frequent_singletons[j])
                    candidate_pairs[candidate_pair] = candidate_pairs.get(candidate_pair, 0) + 1

        "now we have all the candidate pairs, we want to count how much they appear together in the same basket"
        for key in candidate_pairs:
            for item in baskets:
                if key[0] in item and key[1] in item:
                    frequent_pairs[(key[0], key[1])] = frequent_pairs.get((key[0], key[1]), 0) + 1

        "We cancel entries that are not actually frequent"
        temp = [item[0] for item in frequent_pairs.items() if item[1] < len(baskets) * t_hold]
        for item in temp:
            del frequent_pairs[item]

        if frequent_pairs:
            pass

        t_hold = t_hold * 1/2

    return frequent_pairs
