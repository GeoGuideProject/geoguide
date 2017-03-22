from math import sqrt, isnan
from statistics import mean
from fuzzywuzzy import fuzz


def square_rooted(x):
    return sqrt(sum([a * a for a in x]))


def cosine_similarity(x, y):
    numerator = sum(a * b for a, b in zip(x, y))
    denominator = square_rooted(x) * square_rooted(y)
    try:
        return numerator / float(denominator)
    except ZeroDivisionError:
        return 0.0


def cosine_similarity_with_nan(x, y):
    x_dot_y = 0
    x_norm = 0
    y_norm = 0

    for a, b in zip(x, y):
        if isnan(a) or isnan(b):
            continue
        x_dot_y += a * b
        x_norm += a * a
        y_norm += b * b

    x_norm = sqrt(x_norm)
    y_norm = sqrt(y_norm)

    if (x_norm == 0) or (y_norm == 0):
        ratio = 0.0
    else:
        ratio = x_dot_y / (x_norm * y_norm)
    return ratio


def jaccard_similarity(x, y):
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    try:
        return intersection_cardinality / float(union_cardinality)
    except ZeroDivisionError:
        return 0.0


def fuzz_similarity(x, y):
    ratios = []
    for a, b in zip(x, y):
        if not a or not b:
            continue
        r = fuzz.token_set_ratio(a, b) * 0.01
        ratios.append(r)
    if ratios:
        return mean(ratios)
    return 0.0
