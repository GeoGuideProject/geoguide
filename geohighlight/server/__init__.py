# geohighlight/server/__init__.py


#################
#### imports ####
#################

import os
from decouple import config

from flask import Flask, render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads


################
#### config ####
################

app = Flask(
    __name__,
    template_folder='../client/templates',
    static_folder='../client/static'
)


app_settings = config('APP_SETTINGS', 'geohighlight.server.config.ProductionConfig')
app.config.from_object(app_settings)


####################
#### extensions ####
####################

toolbar = DebugToolbarExtension(app)
db = SQLAlchemy(app)


###################
##### uploads #####
###################

datasets = UploadSet('datasets', ('csv',))
configure_uploads(app, (datasets))


###################
### blueprints ####
###################

from geohighlight.server.main.views import main_blueprint
from geohighlight.server.geohighlight.views import geohighlight_blueprint

app.register_blueprint(main_blueprint)
app.register_blueprint(geohighlight_blueprint)


########################
#### error handlers ####
########################

@app.errorhandler(401)
def unauthorized_page(error):
    return render_template("errors/401.html"), 401


@app.errorhandler(403)
def forbidden_page(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error_page(error):
    return render_template("errors/500.html"), 500
