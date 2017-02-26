# geoguide/server/geoguide/views.py

import json
import pandas as pd
import numpy as np
from uuid import uuid4
from flask import request, session, render_template, Blueprint, flash, redirect, url_for, jsonify, abort
from geoguide.server import db, datasets
from flask_uploads import UploadNotAllowed
from geoguide.server.models import Dataset, Attribute, AttributeType
from geoguide.server.geoguide.helpers import save_as_hdf5, path_to_hdf5, harvestine_distance
from geoguide.server.iuga import run_iuga
from geoguide.server.similarity import cosine_similarity, jaccard_similarity
from itertools import chain


geoguide_blueprint = Blueprint('geoguide', __name__,)


@geoguide_blueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    vm = {}
    vm['datasets'] = Dataset.query.all()
    if request.method == 'POST' and 'datasetInputFile' in request.files:
        try:
            uploaded = request.files['datasetInputFile']
            filename = datasets.save(uploaded, name='{}.'.format(uuid4()))
            title = request.form['titleInputText']
            number_of_rows = None
            if request.form['numberRowsInputNumber']:
                number_of_rows = int(request.form['numberRowsInputNumber'])
            latitude_attr = None
            if request.form['latitudeAttrInputText']:
                latitude_attr = request.form['latitudeAttrInputText']
            longitude_attr = None
            if request.form['longitudeAttrInputText']:
                longitude_attr = request.form['longitudeAttrInputText']
            datetime_attr = []
            if request.form['datetimeAttrInputText']:
                datetime_attr = [attr.strip() for attr in request.form['datetimeAttrInputText'].split(',')]
            dataset = Dataset(title, filename, number_of_rows, latitude_attr, longitude_attr)
            db.session.add(dataset)
            db.session.commit()
            for attr in datetime_attr:
                attribute = Attribute(attr, AttributeType.datetime, dataset.id)
                db.session.add(attribute)
                db.session.commit()
            session['SELECTED_DATASET'] = filename
            save_as_hdf5(dataset)
            return redirect(url_for('geoguide.environment'))
        except UploadNotAllowed:
            flash('This file is not allowed.', 'error')
        return redirect(url_for('geoguide.upload'))
    return render_template('geoguide/upload.html', **vm)


@geoguide_blueprint.route('/environment', defaults={'selected_dataset': None})
@geoguide_blueprint.route('/environment/<selected_dataset>')
def environment(selected_dataset):
    if selected_dataset is None:
        if 'SELECTED_DATASET' in session:
            selected_dataset = session['SELECTED_DATASET']
    if selected_dataset is None:
        return redirect(url_for('geoguide.upload'))
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    df = pd.read_hdf(path_to_hdf5(dataset.filename), 'data')
    vm = {}
    vm['dataset_json'] = json.dumps({
        'filename': dataset.filename,
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr,
        'attributes': [dict(description=attr.description, type=attr.type.value) for attr in dataset.attributes]
    })
    vm['dataset_url'] = datasets.url(dataset.filename)
    vm['dataset_headers'] = list(df.select_dtypes(include=[np.number]).columns)
    return render_template('geoguide/environment.html', **vm)


@geoguide_blueprint.route('/environment/<selected_dataset>/<int:index>')
def point_details(selected_dataset, index):
    df = pd.read_hdf(path_to_hdf5(selected_dataset), 'data')
    return df.loc[index].to_json(), 200, {'Content-Type': 'application/json'}


@geoguide_blueprint.route('/environment/<selected_dataset>/<int:index>/iuga')
def point_suggestions(selected_dataset, index):
    k = int(request.args['k'])
    sigma = float(request.args['sigma'])
    limit = float(request.args['limit'])

    if k <= 0 or sigma < 0 or sigma > 1 or limit <= 0:
        abort(401)

    ds = []
    df = pd.read_hdf(path_to_hdf5(selected_dataset), 'data')
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    datetime_columns = [attr.description for attr in dataset.attributes if attr.type == AttributeType.datetime]
    len_datetime_columns = len(datetime_columns)
    point = df.loc[index]
    numeric_columns = list(df.select_dtypes(include=[np.number]).columns)
    numeric_columns = [c for c in numeric_columns if 'latitude' not in c and 'longitude' not in c and not df[c].isnull().any()]
    df = df.loc[:, [dataset.latitude_attr, dataset.longitude_attr, *numeric_columns, *datetime_columns]]
    point_numerics = [point[c] for c in numeric_columns]
    point_datetimes = list(chain.from_iterable([[point[c].hour, point[c].minute, point[c].weekday()] for c in datetime_columns]))
    greatest_distance = 0
    greatest_similarity = 0
    for row in df.itertuples():
        if index == row[0]:
            continue
        if row[1] == 0 or row[2] == 0:
            continue
        distance = harvestine_distance(point[dataset.latitude_attr], point[dataset.longitude_attr],
                                       row[1], row[2])
        row_datetimes = list(chain.from_iterable([[d.hour, d.minute, d.weekday()] for d in row[-len_datetime_columns:]]))
        row_numerics = row[3:-len_datetime_columns]
        similarity_i = (1 + jaccard_similarity(point_datetimes, row_datetimes))
        similarity_ii = (1 + cosine_similarity(point_numerics, row_numerics))
        similarity = similarity_i + similarity_ii
        ds.append((index, row[0], similarity, distance))
        if distance > greatest_distance:
            greatest_distance = distance
        if similarity > greatest_similarity:
            greatest_similarity = similarity

    df_relation = pd.DataFrame(
        ds, columns=['index_a', 'index_b', 'similarity', 'distance']
    ).assign(
        similarity=lambda x: x.similarity / greatest_similarity,
        distance=lambda x: x.distance / greatest_distance
    )

    vm = {}
    vm['similarity'], vm['diversity'], vm['points'] = run_iuga(index, k, limit, sigma, df_relation)
    return jsonify(vm)
