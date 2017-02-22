# geohighlight/server/geohighlight/views.py

import json
from uuid import uuid4
from flask import request, session, render_template, Blueprint, flash, redirect, url_for
from geohighlight.server import db, datasets
from flask_uploads import UploadNotAllowed
from geohighlight.server.models import Dataset


geohighlight_blueprint = Blueprint('geohighlight', __name__,)


@geohighlight_blueprint.route('/upload', methods=['GET', 'POST'])
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
    vm = {}
    vm['dataset_json'] = json.dumps({
        'latitude_attr': dataset.latitude_attr,
        'longitude_attr': dataset.longitude_attr
    })
    vm['dataset_url'] = datasets.url(dataset.filename)
    return render_template('geohighlight/environment.html', **vm)
