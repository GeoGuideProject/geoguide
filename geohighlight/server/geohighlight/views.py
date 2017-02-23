# geohighlight/server/geohighlight/views.py

import json
import pandas as pd
from uuid import uuid4
from flask import request, session, render_template, Blueprint, flash, redirect, url_for, jsonify, abort
from geohighlight.server import db, datasets
from flask_uploads import UploadNotAllowed
from geohighlight.server.models import Dataset
from geohighlight.server.geohighlight.helpers import save_as_hdf5, path_to_hdf5, harvestine_distance
from geohighlight.server.iuga import run_iuga


geohighlight_blueprint = Blueprint('geohighlight', __name__,)


@geohighlight_blueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    vm = {}
    vm['datasets'] = Dataset.query.all()
    if request.method == 'POST' and 'datasetInputFile' in request.files:
        try:
            uploaded = request.files['datasetInputFile']
            filename = datasets.save(uploaded, name='{}.'.format(uuid4()))
            save_as_hdf5(datasets.path(filename))
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
            dataset = Dataset(title, filename, number_of_rows, latitude_attr, longitude_attr)
            db.session.add(dataset)
            db.session.commit()
            session['SELECTED_DATASET'] = filename
            return redirect(url_for('geohighlight.environment'))
        except UploadNotAllowed:
            flash('This file is not allowed.', 'error')
        return redirect(url_for('geohighlight.upload'))
    return render_template('geohighlight/upload.html', **vm)


@geohighlight_blueprint.route('/environment', defaults={'selected_dataset': None})
@geohighlight_blueprint.route('/environment/<selected_dataset>')
def environment(selected_dataset):
    if selected_dataset is None:
        if 'SELECTED_DATASET' in session:
            selected_dataset = session['SELECTED_DATASET']
    if selected_dataset is None:
        return redirect(url_for('geohighlight.upload'))
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    df = pd.read_hdf(path_to_hdf5(dataset.filename), 'data')
    vm = {}
    vm['dataset_json'] = json.dumps({
        'filename': dataset.filename,
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr
    })
    vm['dataset_url'] = datasets.url(dataset.filename)
    vm['dataset_headers'] = list(df.columns.values)
    return render_template('geohighlight/environment.html', **vm)


@geohighlight_blueprint.route('/environment/<selected_dataset>/<int:index>')
def point_details(selected_dataset, index):
    df = pd.read_hdf(path_to_hdf5(selected_dataset), 'data')
    return df.loc[index].to_json(), 200, {'Content-Type': 'application/json'}


@geohighlight_blueprint.route('/environment/<selected_dataset>/<int:index>/iuga')
def point_suggestions(selected_dataset, index):
    k = int(request.args['k'])
    sigma = float(request.args['sigma'])
    limit = float(request.args['limit'])

    if k <= 0 or sigma < 0 or sigma > 1 or limit <= 0:
        abort(401)

    ds = []
    df = pd.read_hdf(path_to_hdf5(selected_dataset), 'data')
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    point = df.loc[index]
    df = df.loc[:, [dataset.latitude_attr, dataset.longitude_attr]]
    greatest_distance = 0

    for row in df.itertuples():
        if index == row[0]:
            continue
        distance = harvestine_distance(point[dataset.latitude_attr], point[dataset.longitude_attr],
                                       row[1], row[2])
        ds.append((index, row[0], distance, distance))
        if distance > greatest_distance:
            greatest_distance = distance

    df_relation = pd.DataFrame(
        ds, columns=['index_a', 'index_b', 'similarity', 'distance']
    ).assign(
        similarity=lambda x: x.similarity / greatest_distance,
        distance=lambda x: x.distance / greatest_distance
    )

    vm = {}
    vm['similarity'], vm['diversity'], vm['points'] = run_iuga(index, k, limit, sigma, df_relation)
    return jsonify(vm)
