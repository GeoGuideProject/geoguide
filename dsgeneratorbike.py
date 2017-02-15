import csv
import math
import mmap
import shutil
import os
# latpick, longpick           = [6, 5]
# latdrop, longdrop           = [10, 9]
# pickup_datetime, dropoff_datetime = [1, 2]
# distance, passenger   = [4, 3]
# fare, tip, total = [12, 15, 17]
biggerdistance, biggersimilarity, firstline, countlines = [0, 0, True, 0]


# getHour function
def getHour(strdate):
    try:
        strdate = strdate.split()
        return strdate[1].split(':')[0]
    except(IndexError):
        return 0


# getHour function
def getMinute(strdate):
    try:
        strdate = strdate.split()
        return int(strdate[1].split(':')[1])
    except(IndexError):
        return 0


# harvestine_distance function, for calculate distance
def harvestine_distance(lat1, lng1, lat2, lng2):
    try:
        dept_lat_rad = math.radians(lat1)
        dept_lng_rad = math.radians(lng1)
        arr_lat_rad = math.radians(lat2)
        arr_lng_rad = math.radians(lng2)
        earth_radius = 3963.1
        d = math.acos(math.cos(dept_lat_rad) * math.cos(dept_lng_rad) * math.cos(arr_lat_rad) * math.cos(arr_lng_rad) + math.cos(dept_lat_rad) *
                      math.sin(dept_lng_rad) * math.cos(arr_lat_rad) * math.sin(arr_lng_rad) + math.sin(dept_lat_rad) * math.sin(arr_lat_rad)) * earth_radius
        return round(d, 2)
    except:
        return 0


def square_rooted(x):
    return round(sqrt(sum([a * a for a in x])), 3)


def cosine_similarity(x, y):
    numerator = sum(a * b for a, b in zip(x, y))
    denominator = square_rooted(x) * square_rooted(y)
    return round(numerator / float(denominator), 3)


def jaccard_similarity(x, y):
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    return intersection_cardinality / float(union_cardinality)


def setBiggerValue(disval, simval):
    global biggerdistance
    global biggersimilarity
    if(biggerdistance < disval):
        biggerdistance = disval
    if(biggersimilarity < simval):
        biggersimilarity = simval

# North Limit: 40.915031, -73.910336
# East Limit: 40.739040, -73.700208
# South Limit:  40.495730, -74.248575
# West Limit: 40.508258, -74.255698


def ignorePoint(p1, p2, p3, p4):
    try:
        if((p1 < 40.495730) or (p1 > 40.915031) or (p3 < 40.495730) or (p3 > 40.915031)):
            return True
        elif((p2 < -74.255698) or (p2 > -73.700208) or (p4 < -74.255698) or (p4 > -73.700208)):
            return True
        else:
            return False
    except Exception as ex:
        return True

# "0tripduration","1starttime","2stoptime","3start station id","4start station name",
# "5start station latitude","6start station longitude","7end station id","8end station name",
# "9end station latitude","10end station longitude","11bikeid","12usertype","13birth year","14gender"
temp = csv.writer(open("tmp/temp.csv", "w", newline=''))
index = csv.writer(open("dataanalysis/index.csv", "w", newline=''))
index.writerow(['p_index', 'dataset_line_index', 'latitude',
                'longitude', 'hour', 'duration', 'isPickUp'])
latpick, longpick = [5, 6]
latdrop, longdrop = [9, 10]
pickup_datetime, dropoff_datetime = [1, 2]
# reading dataset
input_dataset = open('tmp/arquivo.csv', newline='')

# HEADER definition and its features
header_line = input_dataset.readline()
header_features = header_line.split(",")
# for feature in header_features:
#    print feature

#-------------------------------------------------------------------------
#----------------------------    Ignoring Points & creating index.csv    -
#-------------------------------------------------------------------------


print("Points ignored...")
countlines = 0
for row in iter(input_dataset.readline, ''):
    countlines += 1
    ignoreIndex = 0
    row = row.replace('"', '')  # Remove all quotes
    reading_line = row.split(",")
    try:
        if (ignorePoint(float(reading_line[latpick]),
                        float(reading_line[longpick]),
                        float(reading_line[latdrop]),
                        float(reading_line[longdrop]))):
            ignoreIndex += 2
            print(float(reading_line[latpick]), float(reading_line[longpick]),
                  float(reading_line[latdrop]), float(reading_line[longdrop]))
        else:
            index.writerow([
                (countlines * 2) - 1 - ignoreIndex,
                countlines,
                reading_line[latpick],
                reading_line[longpick],
                reading_line[pickup_datetime],
                1
            ])
            index.writerow([
                (countlines * 2) - ignoreIndex,
                countlines,
                reading_line[latdrop],
                reading_line[longdrop],
                reading_line[dropoff_datetime],
                0
            ])
    except Exception as ex:
        ignoreIndex += 2
        print(float(reading_line[latdrop]), float(reading_line[longdrop]),
              float(reading_line[latdrop]), float(reading_line[longdrop]))

#-------------------------------------------------------------------------
#----------------------------    Reading Data Set again    ---------------
#-------------------------------------------------------------------------

# reading generated index.csv
print("Creating index_aux.csv to calculate similarities...")
shutil.copyfile('dataanalysis/index.csv', 'tmp/index_aux.csv')


print("Re-opening index.csv to start operations...")
_index = open('dataanalysis/index.csv', newline='')
_index_features = _index.readline().split(",")

#-------------------------------------------------------------------------
#----------------------------    Calculating Similarities    -------------
#-------------------------------------------------------------------------

# indexes
#index.writerow(['p_index', 'dataset_line_index' , 'latitude', 'longitude', 'hour', 'duration', 'isPickUp'])
p_index, dataset_line_index, latitude,\
    longitude, hour, duration, isPickUp = range(7)
pointValue = 1
aux_pointValue = 1

_index = _index.readlines()
print("Starting to calculate the similarities ...")
for i in range(countlines):
    _index_values = _index[i].split(",")
    # INDEX_AUX
    #print("Opening index_aux.csv to start operations...")
    index_aux = open('tmp/index_aux.csv', newline='')
    index_aux_features = index_aux.readline().split(",")

    index_aux = index_aux.readlines()
    print("Still calculating the similarities [missing features...]",
          (countlines - pointValue))
    for j in range(pointValue, countlines):
        index_aux_values = index_aux[j].split(",")
        #partsimilarity =  (  (int(_index_values[passenger]) + int(index_aux_values[passenger])) + (getHour(_index_values[hour]) / getHour(index_aux_values[hour]))  )
        #partsimilarity =  ((int(index_aux_values[passenger]) * 2) + 1)
        distance = harvestine_distance(float(_index_values[latitude]),
                                       float(_index_values[longitude]),
                                       float(index_aux_values[latitude]),
                                       float(index_aux_values[longitude]))

        similarity = harvestine_distance(float(_index_values[latitude]),
                                         float(_index_values[longitude]),
                                         float(index_aux_values[latitude]),
                                         float(index_aux_values[longitude]))

        temp.writerow([
            _index_values[p_index],
            index_aux_values[p_index],
            distance,
            similarity])

        setBiggerValue(distance, similarity)

    pointValue += 1

#-------------------------------------------------------------------------
#----------------------------------    Parsing Final DS    ---------------
#-------------------------------------------------------------------------


print("Parsing distance and similarity from temp.csv to ds.csv ")
ds = open("dataanalysis/ds.csv", "w", newline='')
dscsv = csv.writer(ds)
with open('tmp/temp.csv', newline='') as temp_ds:
    for row in csv.reader(temp_ds):
        try:
            camp1 = float(row[2]) / biggerdistance
            camp1 = "%.10f" % camp1
        except:
            camp1 = -1

        try:
            camp2 = float(row[3]) / biggersimilarity
            camp2 = "%.10f" % camp2
        except:
            camp2 = -1
        if(camp1 == -1) or (camp2 == -1):
            None
        else:
            dscsv.writerow([row[0], row[1], camp1, camp2])
ds.close()

os.remove('tmp/temp.csv')
os.remove('tmp/index_aux.csv')

#-------------------------------------------------------------------------
#----------------------------    Running experiments    ------------------
#-------------------------------------------------------------------------

arquivos = []
print("Running experiments.")

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ANALYSIS = os.path.join(APP_ROOT, 'dataanalysis')
dir = os.path.join(APP_ANALYSIS, 'dspoints')

try:
    os.stat(dir)
except:
    os.mkdir(dir)

for val in range(0, 10):
    strfile = 'dataanalysis/dspoints/' + str(val) + '_' + str(val + 1) + '.csv'
    arquivos.append(csv.writer(open(strfile, 'w', newline='')))
    arquivos[val].writerow(['p1', 'p2'])


with open('dataanalysis/ds.csv', newline='') as f7:
    for row in csv.reader(f7):
        row2 = float(row[2])
        row3 = float(row[3])
        if (0.0 <= row3 < 0.1):
            arquivos[0].writerow([row[0], row[1]])
        elif (0.1 <= row3 < 0.2):
            arquivos[1].writerow([row[0], row[1]])
        elif (0.2 <= row3 < 0.3):
            arquivos[2].writerow([row[0], row[1]])
        elif (0.3 <= row3 < 0.4):
            arquivos[3].writerow([row[0], row[1]])
        elif (0.4 <= row3 < 0.5):
            arquivos[4].writerow([row[0], row[1]])
        elif (0.5 <= row3 < 0.6):
            arquivos[5].writerow([row[0], row[1]])
        elif (0.6 <= row3 < 0.7):
            arquivos[6].writerow([row[0], row[1]])
        elif (0.7 <= row3 < 0.8):
            arquivos[7].writerow([row[0], row[1]])
        elif (0.8 <= row3 < 0.9):
            arquivos[8].writerow([row[0], row[1]])
        elif (0.9 <= row3 <= 1):
            arquivos[9].writerow([row[0], row[1]])

print("Finish!")
