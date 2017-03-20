from math import sqrt, isnan


def square_rooted(x):
    return round(sqrt(sum([a * a for a in x])), 3)


def cosine_similarity(x, y):
    numerator = sum(a * b for a, b in zip(x, y))
    denominator = square_rooted(x) * square_rooted(y)
    try:
        return round(numerator / float(denominator), 3)
    except ZeroDivisionError:
        return 0.0


def cosine_similarity_with_nan(x, y):
    m = len(x)
    x_dot_y = 0
    x_norm = 0
    y_norm = 0
    for i in range(m):
        if (isnan(x[i])) or (isnan(y[i])):
            continue
        x_dot_y += x[i] * y[i]
        x_norm += x[i] * x[i]
        y_norm += y[i] * y[i]

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
