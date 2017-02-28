# Different functions for diversity may be defined here.
# A diversity function gets a list of objects and return one float value between zero and one.
# A value close to one means higher diversity.
# Input for user groups: redundant list of all members of all groups.
# Input for spatiotemporal data: list of distance values.


# diversity definition for spatiotemporal data
def diversity_calculator_geo(elements):
    count = len(elements)
    sum = 0
    for value in elements:
        sum += value
    average = sum / count
    return average


# diversity definition for user data as jaccard (as in CIKM'15 paper)
def diversity_calculator_jaccard(users_list):
    users_set = set(users_list)
    unqiue_count = len(users_set)
    all_count = len(users_list)
    jaccard = float(unqiue_count) / float(all_count)
    return jaccard


# diversity definition for user data as exponential (as in PKDD'16 paper)
def diversity_calculator_expo(users_list):
    users_set = set(users_list)
    unqiue_count = len(users_set)
    all_count = len(users_list)
    nb_overlaps = all_count - unqiue_count
    diversity_expo = 1.0 / float(1 + nb_overlaps)
    return diversity_expo


def diversity(elements):
    return diversity_calculator_expo(elements)
    # return diversity_calculator_jaccard(elements)
    # return diversity_calculator_expo(elements)
