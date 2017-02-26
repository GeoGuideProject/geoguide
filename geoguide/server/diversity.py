"""
Different functions for diversity may be defined here.

A diversity function gets a list of objects and return one float value between zero and one
A value close to one means higher diversity.

Input for user groups: redundant list of all members of all groups.
Input for spatiotemporal data: list of distance values.
"""


def diversity_calculator_geo(elements):
    """
    Diversity definition for spatiotemporal data.
    """
    count = len(elements)
    average = sum(elements) / count
    return average


def diversity_calculator_jaccard(users_list):
    """
    Diversity definition for user data as jaccard (as in CIKM'15 paper).
    """
    users_set = set(users_list)
    unique_count = len(users_set)
    all_count = len(users_list)
    jaccard = unique_count / all_count
    return jaccard


def diversity_calculator_expo(users_list):
    """
    Diversity definition for user data as exponential (as in PKDD'16 paper).
    """
    users_set = set(users_list)
    unique_count = len(users_set)
    all_count = len(users_list)
    nb_overlaps = all_count - unique_count
    diversity_expo = 1.0 / (1 + nb_overlaps)
    return diversity_expo


def diversity(elements):
    return diversity_calculator_expo(elements)
