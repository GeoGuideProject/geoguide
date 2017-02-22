# geohighlight/server/geohighlight/views.py

from uuid import uuid4
from flask import request, render_template, Blueprint, flash, redirect, url_for
from geohighlight.server import datasets
from flask_uploads import UploadNotAllowed
from geohighlight.server.models import Dataset


geohighlight_blueprint = Blueprint('geohighlight', __name__,)


@geohighlight_blueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'dataset' in request.files:
        try:
            uploaded = request.files['dataset']
            filename = datasets.save(uploaded, name='{}.'.format(uuid4()))
            dataset = Dataset(filename)
            flash('Dataset saved in {}.'.format(datasets.url(filename)), 'success')
        except UploadNotAllowed:
            flash('This file is not allowed.', 'error')
        return redirect(url_for('geohighlight.upload'))
    return render_template('geohighlight/upload.html')
