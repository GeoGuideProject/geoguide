from math import sqrt


def square_rooted(x):
    return round(sqrt(sum([a * a for a in x])), 3)


def cosine_similarity(x, y):
    numerator = sum(a * b for a, b in zip(x, y))
    denominator = square_rooted(x) * square_rooted(y)
    try:
        return round(numerator / float(denominator), 3)
    except ZeroDivisionError:
        return 0.0


def jaccard_similarity(x, y):
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    try:
        return intersection_cardinality / float(union_cardinality)
    except ZeroDivisionError:
        return 0.0
