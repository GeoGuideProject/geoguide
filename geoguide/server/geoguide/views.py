# geoguide/server/geoguide/views.py

import json
import pandas as pd
import numpy as np
from uuid import uuid4
from flask import request, session, render_template, Blueprint, flash, redirect, url_for, jsonify, abort
from geoguide.server import db, datasets
from flask_uploads import UploadNotAllowed
from geoguide.server.models import Dataset, Attribute, AttributeType
from geoguide.server.geoguide.helpers import save_as_hdf, path_to_hdf, harvestine_distance, index_dataset
from geoguide.server.iuga import run_iuga
from geoguide.server.similarity import cosine_similarity, jaccard_similarity
from itertools import chain
from threading import Thread


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
            if request.form['latitudeAttrSelect']:
                latitude_attr = request.form['latitudeAttrSelect']
            longitude_attr = None
            if request.form['longitudeAttrSelect']:
                longitude_attr = request.form['longitudeAttrSelect']
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
            save_as_hdf(dataset)
            Thread(target=lambda: index_dataset(dataset)).start()
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
    df = pd.read_hdf(path_to_hdf(dataset), 'data')
    vm = {}
    vm['dataset_headers'] = list(df.select_dtypes(include=[np.number]).columns)
    vm['dataset_headers'] = [c for c in vm['dataset_headers'] if 'latitude' not in c and 'longitude' not in c]
    vm['dataset_json'] = json.dumps({
        'filename': dataset.filename,
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr,
        'indexed': (dataset.indexed_at is not None),
        'attributes': [dict(description=attr.description, type=attr.type.value) for attr in dataset.attributes],
        'headers': vm['dataset_headers'],
    })
    vm['dataset_url'] = datasets.url(dataset.filename)
    return render_template('geoguide/environment.html', **vm)


@geoguide_blueprint.route('/environment/<selected_dataset>/details')
def dataset_datails(selected_dataset):
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    return jsonify({
        'filename': dataset.filename,
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr,
        'indexed': (dataset.indexed_at is not None),
        'attributes': [dict(description=attr.description, type=attr.type.value) for attr in dataset.attributes]
    })

@geoguide_blueprint.route('/environment/<selected_dataset>/<int:index>')
def point_details(selected_dataset, index):
    df = pd.read_hdf(path_to_hdf(selected_dataset), 'data')
    return df.loc[index].to_json(), 200, {'Content-Type': 'application/json'}


@geoguide_blueprint.route('/environment/<selected_dataset>/<int:index>/iuga')
def point_suggestions(selected_dataset, index):
    k = int(request.args['k'])
    sigma = float(request.args['sigma'])
    limit = float(request.args['limit'])

    filtered_points = request.args.get('filtered_points', default='')
    if filtered_points:
        filtered_points = [int(x) for x in filtered_points.split(',')]

    if k <= 0 or sigma < 0 or sigma > 1 or limit <= 0:
        abort(401)

    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    if dataset.indexed_at is None:
        return jsonify(dict(message='Not ready yet.')), 202
    df_relation = pd.read_hdf(path_to_hdf(dataset), 'relation')
    if filtered_points:
        df_relation = df_relation[(df_relation['index_a'].isin(filtered_points)) & (df_relation['index_b'].isin(filtered_points))]
    vm = {}
    vm['similarity'], vm['diversity'], vm['points'] = run_iuga(index, k, limit, sigma, df_relation)
    return jsonify(vm)
