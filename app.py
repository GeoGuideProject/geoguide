# Force python 2.7 to work with utf-8
import sys
import os
import csv
import re
import json
import imp
import threading
import subprocess
import uuid
import iugaMod
from flask import Flask, render_template, request, send_from_directory
from werkzeug import secure_filename

app = Flask(__name__)

# Directories config
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_TMP = os.path.join(APP_ROOT, 'tmp')
APP_ANALYSIS = os.path.join(APP_ROOT, 'dataanalysis')

app.config['ALLOWED_EXTENSIONS'] = set(['csv'])

# Thread to generate ds archives
background_scripts = {}
controleRun = -1
#
datasettype = 0
# Making dspoints directory if its not exist
dir = os.path.join(APP_ANALYSIS, 'dspoints')

try:
    os.stat(dir)
except:
    os.mkdir(dir)
# Send no-cache request in header


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


def run_script(id):
    global controleRun
    controleRun = id
    firstCollumnHeader = ""
    with open(os.path.join(APP_TMP, 'arquivo.csv')) as f:
        for row in csv.reader(iter(f.readline, '')):
            firstCollumnHeader = row[0]
            print(firstCollumnHeader)
            break
    if("vendor_id" == firstCollumnHeader):
        archivedir = APP_ROOT + "/dsgenerator.py"
    else:
        archivedir = APP_ROOT + "/dsgeneratorbike.py"
    subprocess.call(["python", archivedir])
    background_scripts[id] = True


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def file_proc():
    global datasettype
    examplevalues = []
    options = []
    mapsoptions = []
    datasettype = 0
    with open(os.path.join(APP_TMP, 'arquivo.csv')) as f:
        firstline = True
        for row in csv.reader(iter(f.readline, '')):
            if(firstline == True):
                tempoptions = row
                firstline = False
            else:
                examplevalues = row
                break
    # Select numeric fields and add to options list
    for index, value in enumerate(examplevalues):
        try:
            float(value)
            options.append(tempoptions[index])
        except:
            None
    if("vendor_id" == tempoptions[0]):
        options.append(tempoptions[1])
        options.append(tempoptions[2])
        datasettype = 1
    elif("tripduration" == tempoptions[0]):
        options.append(tempoptions[1])
        options.append(tempoptions[2])
        datasettype = 2
    print("DATASET: ", datasettype)
    # Select in options list the possible values for lat and long, if not
    # found show all int values
    for index, value in enumerate(tempoptions):
        if(value.find("lat") != -1):
            mapsoptions.append(tempoptions[index])
        elif(value.find("long") != -1):
            mapsoptions.append(tempoptions[index])
    if(len(mapsoptions) < 2):
        mapsoptions = []
        for index, value in enumerate(examplevalues):
            try:
                value = float(value)
                try:
                    int(value)

                except:
                    mapsoptions.append(tempoptions[index])
            except:
                None
    if(len(mapsoptions) < 2):
        mapsoptions = options
    return render_template('select.html', option_list=options, mapsoptions=mapsoptions)


@app.route('/')
def index():
    formatsmsg = 'Only accept: '
    for x in app.config['ALLOWED_EXTENSIONS']:
        formatsmsg += ' ' + x.upper()
    return render_template('index.html', formatsmsg=formatsmsg)


@app.route('/selectdata', methods=['POST', 'GET'])
def selectdata():
    global datasettype
    print(request.form.get('filter1'), request.form.get('filter2'))
    filter = [request.form.get('filter1'), request.form.get(
        'filter2'), request.form.get('filter3'), request.form.get('filter4')]
    positions = [request.form.get('latitude1'),  request.form.get(
        'longitude1'),  request.form.get('latitude2'),  request.form.get('longitude2')]
    return render_template('charts.html', csvfilename='arquivo.csv', filter=filter, positions=positions, datasettype=datasettype)


@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(APP_ROOT + '/arquivo.csv')
        if(request.form.get('botao') == "Charts and Maps"):
            return file_proc()
        else:
            id = str(uuid.uuid4())
            background_scripts[id] = False
            threading.Thread(target=lambda: run_script(id)).start()
            return send_from_directory(APP_ANALYSIS, 'loading.html')
    else:
        return render_template('index.html', formatsmsg='Format not suported! Try again!')


@app.route('/<path:directory>')
def sendfiles(directory):
    return send_from_directory(APP_ROOT, directory)


@app.route('/isfinish', methods=['POST'])
def sendstatus():
    global controleRun
    if background_scripts[controleRun]:
        return json.dumps({'success': False}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': True}), 201, {'ContentType': 'application/json'}


@app.route('/runiuga', methods=['GET'])
def runiuga():
    # Import IUGA   - Configs
    input_g = int(request.args.get('pointchose'))
    time_limit = int(request.args.get('timelimit'))  # in miliseconds
    k = int(request.args.get('kvalue'))            # number of returned records
    lowest_acceptable_similarity = float(request.args.get('sigma'))
    input_file = APP_ROOT + "/dataanalysis/ds.csv"  
    compostReturn = iugaMod.runIuga(input_g, k, time_limit, lowest_acceptable_similarity, input_file)
    return json.dumps({"similarity": compostReturn[0], "diversity": compostReturn[1], "array": (compostReturn[2])}), 200, {'ContentType': 'application/json'}


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', use_reloader=True, port=port)
