# project/server/user/views.py


#################
#### imports ####
#################

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from flask_login import login_user, logout_user, login_required

from geoguide.server import bcrypt, db
from geoguide.server.models import User

################
#### config ####
################

user_blueprint = Blueprint('user', __name__,)


################
#### routes ####
################

@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(email=request.form['email'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Thank you for registering.', 'success')
        return redirect(url_for("geoguide.upload"))
    return render_template('user/register.html')


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(
                user.password, request.form['password']):
            login_user(user)
            flash('You are logged in. Welcome!', 'success')
            return redirect(url_for('geoguide.upload'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('user/login.html', email=request.form['email'])
    return render_template('user/login.html')


@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out. Bye!', 'success')
    return redirect(url_for('main.home'))
