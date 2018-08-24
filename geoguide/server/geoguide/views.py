# geoguide/server/geoguide/views.py

import json
import os.path
import pandas as pd
import numpy as np
import geojson

from shapely.geometry import asShape
from geoalchemy2.shape import from_shape

from uuid import uuid4
from flask import request, session, render_template, Blueprint, flash, redirect, url_for, jsonify, abort
from geoguide.server import app, db, datasets, logging
from flask_uploads import UploadNotAllowed
from geoguide.server.models import Dataset, Attribute, AttributeType, Session, Polygon, IDR
from geoguide.server.services import get_next_polygon_and_idr_iteration
from geoguide.server.geoguide.helpers import save_as_hdf, path_to_hdf, save_as_sql
from geoguide.server.iuga import run_iuga
from sqlalchemy import create_engine
from flask_login import login_required, current_user

SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']
DEBUG = app.config['DEBUG']
USE_SQL = app.config['USE_SQL']
geoguide_blueprint = Blueprint('geoguide', __name__,)


@geoguide_blueprint.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
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
            save_as_sql(dataset, request.form.getlist('selectionAttrInputCheckbox')) if USE_SQL else save_as_hdf(dataset)
            return redirect(url_for('geoguide.environment'))
        except UploadNotAllowed:
            flash('This file is not allowed.', 'error')
        return redirect(url_for('geoguide.upload'))
    vm = {}
    vm['datasets'] = current_user.datasets
    needs_reload = False
    for dataset in vm['datasets']:
        if not os.path.isfile(datasets.path(dataset.filename)):
            db.session.delete(dataset)
            needs_reload = True
    if needs_reload:
        db.session.commit()
        vm['datasets'] = current_user.datasets
    return render_template('geoguide/upload.html', **vm)


@geoguide_blueprint.route('/environment', defaults={'selected_dataset': None})
@geoguide_blueprint.route('/environment/<selected_dataset>')
@login_required
def environment(selected_dataset):
    if selected_dataset is None:
        if 'SELECTED_DATASET' in session:
            selected_dataset = session['SELECTED_DATASET']
    if selected_dataset is None:
        return redirect(url_for('geoguide.upload'))
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()

    feedback_session = Session(dataset=dataset)
    db.session.add(feedback_session)
    db.session.commit()

    df = pd.read_csv(datasets.path(dataset.filename))
    vm = {}
    vm['dataset_headers'] = list(df.select_dtypes(include=[np.number]).columns)
    vm['dataset_headers'] = [c for c in vm['dataset_headers'] if 'latitude' not in c and 'longitude' not in c and 'id' not in c and not df[c].isnull().any() and df[c].unique().shape[0] > 3]
    vm['dataset_json'] = json.dumps({
        'filename': dataset.filename,
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr,
        'indexed': (dataset.indexed_at is not None),
        'attributes': [dict(description=attr.description, visible=attr.visible, type=dict(value=attr.type.value, description=attr.type.name)) for attr in dataset.attributes],
        'headers': vm['dataset_headers'],
    })
    vm['dataset_url'] = datasets.url(dataset.filename)
    return render_template('geoguide/environment.html', **vm)


@geoguide_blueprint.route('/environment/<selected_dataset>/details')
@login_required
def dataset_details(selected_dataset):
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    return jsonify({
        'filename': dataset.filename,
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr,
        'indexed': (dataset.indexed_at is not None),
        'attributes': [dict(description=attr.description, visible=attr.visible, type=dict(value=attr.type.value, description=attr.type.name)) for attr in dataset.attributes],
    })


@geoguide_blueprint.route('/environment/<selected_dataset>/<int:index>')
@login_required
def point_details(selected_dataset, index):
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    df = pd.read_csv(datasets.path(dataset.filename))
    return df.loc[index].to_json(), 200, {'Content-Type': 'application/json'}


@geoguide_blueprint.route('/environment/<selected_dataset>/<int:index>/iuga', methods=['POST'])
@login_required
def point_suggestions(selected_dataset, index):
    k = int(request.args['k'])
    sigma = float(request.args['sigma'])
    limit = float(request.args['limit'])

    json_data = request.get_json(True, True)

    filtered_points = json_data.get('filtered_points', '')
    filtered_points = [int(x) for x in filtered_points.split(',') if x]

    clusters = json_data.get('clusters', '')
    clusters = [[float(x) for x in c.split(':') if x] for c in clusters.split(',') if c]
    if DEBUG:
        print(clusters)

    if k <= 0 or sigma < 0 or sigma > 1 or limit <= 0:
        abort(401)

    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()
    if dataset.indexed_at is None:
        return jsonify(dict(message='Not ready yet.')), 202

    vm = {}
    vm['similarity'], vm['diversity'], vm['points'] = run_iuga(
        index, k, limit, sigma, dataset,
        filtered_points=filtered_points,
        clusters=clusters
    )
    return jsonify(vm)


@geoguide_blueprint.route('/environment/<selected_dataset>/points', methods=['GET', 'POST'])
@login_required
def point_by_polygon(selected_dataset):
    dataset = Dataset.query.filter_by(filename=selected_dataset).first_or_404()

    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    table_name = 'datasets.' + dataset.filename.rsplit('.', 1)[0]

    json_data = request.get_json(True, True)
    polygon_path = json_data.get('polygon', '')
    polygon_path = polygon_path.split(',') if polygon_path is not '' else []
    polygon = ''

    filtered_points = json_data.get('filtered_points', '')
    filtered_points = [int(x) for x in filtered_points.split(',') if x]

    if len(polygon_path) > 2:
        polygon_path.append(polygon_path[0])
        polygon = 'POLYGON(({}))'.format(','.join(['{} {}'.format(*p.split(':')[::-1]) for p in polygon_path]))
    else:
        return jsonify(dict(points=[], count=0)), 400

    cursor = engine.execute('''
    select geoguide_id, {}, {}
    from "{}"
    where ST_Contains('{}', geom)
    '''.format(
        dataset.latitude_attr,
        dataset.longitude_attr,
        table_name,
        polygon))

    points = [list(x[1:]) for x in cursor if len(filtered_points) > 0 and (x[0] in filtered_points)]
    return jsonify(dict(points=points, count=len(points)))


@geoguide_blueprint.route('/environment/<selected_dataset>/mouseClusters', methods=['POST'])
@login_required
def mouse_clusters(selected_dataset):
    # request.args
    data = request.get_json(True, True)
    iteration = get_next_polygon_and_idr_iteration()
    intersections = data['intersections']
    polygons = data['polygons']

    get_geom = lambda f: from_shape(asShape(geojson.loads(json.dumps(f['geometry']))))

    new_idrs = []
    for feature in intersections:
        idr = IDR(geom=get_geom(feature), iteration=iteration)
        # db.session.add(idr)
        new_idrs.append(idr)

    db.session.add_all(new_idrs)
    db.session.commit()

    new_polygons = []
    for feature in polygons:
        polygon = Polygon(geom=get_geom(feature), iteration=iteration)
        # db.session.add(polygon)
        new_polygons.append(polygon)

    db.session.add_all(new_polygons)
    db.session.commit()

    for polygon in new_polygons:
        from geoguide.server.services import create_polygon_profile
        create_polygon_profile(polygon.id)

    return jsonify(dict(json=data, args=request.args))
