# geoguide/server/main/views.py


#################
#### imports ####
#################

from flask import Blueprint, redirect, url_for


################
#### config ####
################

main_blueprint = Blueprint('main', __name__,)


################
#### routes ####
################


@main_blueprint.route('/')
def home():
    return redirect(url_for('geoguide.upload'))
