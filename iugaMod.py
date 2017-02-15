#!/usr/bin/env python3
import datetime
import diversity
from random import randint


def get_distances_of(elements, k, distance_by_id):
    my_distances = []
    for i in range(k):
        my_distances.append(distance_by_id[elements[i]])
    return my_distances


def make_new_records(elements, new_element, k, records):
    output = {}
    for i in range(k):
        output[i] = elements[i]
    replacement = randint(0, k - 1)
    output[replacement] = records[new_element]
    return output


def show(elements, k, similarity_by_id, distance_by_id):
    min_similarity = 1
    out = "[ "
    for i in range(0, k):
        out += str(elements[i]) + " "
        if similarity_by_id[elements[i]] < min_similarity:
            min_similarity = similarity_by_id[elements[i]]
    out += "]"
    out += " similarity: " + str() + str(min_similarity)
    my_distances = get_distances_of(elements, k, distance_by_id)
    my_diversity = diversity.diversity(my_distances)
    out += " diversity: " + str(round(my_diversity, 2))
    return out


def runIuga(input_g, kvalue, time_limit, lowest_acceptable_similarity, input_file):
    # parameters
    k = kvalue
    		# indexing file
    # should the algorithm stop if it reaches the end of the index (i.e.,
    # scanning all records once)
    stop_visiting_once = False

    # Note that in case of user group analysis, each group is a record. In
    # case of spatiotemporal data, each geo point is a record.

    # variables
    # the ID of current k records will be recorded in this object.
    current_records = {}
    # ths ID of next potential k records will be recorded in this object.
    new_records = {}
    total_time = 0.0			# total execution time

    # dimensions
    similarities = {}
    distances = {}

    # read input file
    with open(input_file) as f:
        for line in f:
            line = line.strip()
            parts = line.split(",")
            from_id = int(parts[0])
            if from_id > input_g:
                break
            to_id = int(parts[1])
            similarity = float(parts[2])
            distance = float(parts[3])
            similarities[to_id] = similarity
            distances[to_id] = distance

    # sorting similarities and distances in descending order
    similarities_sorted = sorted(
        similarities.items(), key=lambda x: x[1], reverse=True)
    distances_sorted = sorted(
        distances.items(), key=lambda x: x[1], reverse=True)

    # begin - prepare lists for easy retrieval
    records = {}
    similarity_by_id = {}
    distance_by_id = {}

    cnt = 0
    for value in similarities_sorted:
        records[cnt] = value[0]
        similarity_by_id[value[0]] = value[1]
        cnt += 1

    for value in distances_sorted:
        distance_by_id[value[0]] = value[1]
    # begin - prepare lists for easy retrieval

    print(len(records), "records retrieved and indexed.")

    # begin - retrieval functions

    # end - retrieval functions

    # initialization by k most similar records
    for i in range(k):
        current_records[i] = records[i]

    print("begin:", show(current_records, k, similarity_by_id, distance_by_id))

    # greedy algorithm
    pointer = k - 1
    nb_iterations = 0
    while total_time < time_limit and pointer < len(records):
        nb_iterations += 1
        pointer += 1
        redundancy_flag = False
        for i in range(0, k):
            if current_records[i] == records[pointer]:
                redundancy_flag = True
                break
        if redundancy_flag:
            continue
        begin_time = datetime.datetime.now()
        current_distances = get_distances_of(
            current_records, k, distance_by_id)
        current_diversity = diversity.diversity(current_distances)
        new_records = make_new_records(current_records, pointer, k, records)
        new_distances = get_distances_of(new_records, k, distance_by_id)
        new_diversity = diversity.diversity(new_distances)
        if new_diversity > current_diversity:
            current_records = new_records
        end_time = datetime.datetime.now()
        duration = (end_time - begin_time).microseconds / 1000.0
        total_time += duration
        if similarity_by_id[records[pointer]] < lowest_acceptable_similarity:
            if not stop_visiting_once:
                pointer = k
            else:
                break

    print("end:", show(current_records, k, similarity_by_id, distance_by_id))
    print("execution time (ms)", total_time)
    print("# iterations", nb_iterations)

    min_similarity = 1
    dicToArray = []
    for i in range(k):
        if similarity_by_id[current_records[i]] < min_similarity:
            min_similarity = similarity_by_id[current_records[i]]
        dicToArray.append(current_records[i])
    my_distances = get_distances_of(current_records, k, distance_by_id)
    my_diversity = diversity.diversity(my_distances)
    return [min_similarity, round(my_diversity, 2), dicToArray]
