import logging
import os
from datetime import timedelta
from typing import Optional

import cuwais.common
import redis
from flask import Flask, render_template, request, abort, Response, session, redirect
from flask_session import Session

from server import login

app = Flask(
    __name__,
    template_folder="templates"
)
with open("/run/secrets/secret_key") as secrets_file:
    secret = "".join(secrets_file.readlines())
    app.secret_key = secret
    app.config["SECRET_KEY"] = secret
app.config["DEBUG"] = os.getenv('DEBUG') == 'True'
app.config["TESTING"] = os.getenv('TESTING') == 'True'

app.config["SESSION_COOKIE_NAME"] = "cuwais_session"
app.config["SERVER_NAME"] = str(os.getenv('SERVER_NAME'))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)
app.config["SESSION_TYPE"] = 'redis'
app.config["SESSION_REDIS"] = redis.Redis(host='redis', port=6379)
sess = Session(app)

logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.WARNING)


def save_user(user):
    session["cuwais_user"] = cuwais.common.encode(user)


def get_user() -> Optional[cuwais.common.User]:
    cuwais_user = cuwais.common.decode(session.get("cuwais_user", "null"))
    return cuwais_user


def remove_user():
    session.pop("cuwais_user", None)


def make_nav_item(text, icon=None, active=False, link='#', data_toggle=None):
    return dict(text=text, icon=icon, active=active, link=link, data_toggle=data_toggle)


def make_nav_item_from_name(name, current_dir):
    is_active = (name == current_dir)
    link = f'/{name}' if not is_active else '#'
    return make_nav_item(text=name.capitalize(), link=link, active=is_active)


def make_l_nav(user: Optional[cuwais.common.User], current_dir):
    places = []
    if user is not None:
        places += ['leaderboard', 'submissions']
    places += ['about']

    items = [make_nav_item_from_name(name, current_dir) for name in places]
    return items


def make_r_nav(user: Optional[cuwais.common.User], current_dir):
    items = []
    if user is None:
        items.append(
            make_nav_item(text='Log In', icon='fa fa-sign-in', link='#loginModal', data_toggle='modal'))
    else:
        items.append(
            make_nav_item(text=user.display_name, link='/me', active=(current_dir == 'me')))
        items.append(
            make_nav_item(text='Log Out', icon='fa fa-sign-out', link='/logout'))
    return items


def extract_session_objs(current_dir):
    user = get_user()
    return dict(
        user=user,
        l_nav=make_l_nav(user, current_dir),
        r_nav=make_r_nav(user, current_dir)
    )


def ensure_logged_in(f):
    def f_new():
        user = get_user()
        if user is None:
            return render_template(
                'login-required.html',
                **extract_session_objs('login-required')
            )
        return f()

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


@app.route('/')
def index():
    user = get_user()
    if user is not None:
        return redirect('/leaderboard')
    return redirect('/about')


@app.route('/about')
def about():
    return render_template(
        'about.html',
        **extract_session_objs('about')
    )


@app.route('/leaderboard')
@ensure_logged_in
def leaderboard():
    return render_template(
        'leaderboard.html',
        **extract_session_objs('leaderboard')
    )


@app.route('/submissions')
@ensure_logged_in
def submissions():
    return render_template(
        'submissions.html',
        **extract_session_objs('submissions')
    )


@app.route('/me')
@ensure_logged_in
def me():
    return render_template(
        'me.html',
        **extract_session_objs('me')
    )


@app.route('/logout')
def logout():
    remove_user()

    return render_template(
        'logout.html',
        **extract_session_objs('logout')
    )


@app.route('/api/login_google', methods=['POST'])
def login_google():
    json = request.get_json()
    if 'idtoken' not in json:
        abort(400)
    token = json.get('idtoken')

    user = login.get_user_from_google_token(token)
    save_user(user)

    encoded = cuwais.common.encode(user)

    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_leaderboard')
def get_leaderboard():
    # TODO: Cache this
    scoreboard = cuwais.common.get_scoreboard()

    encoded = cuwais.common.encode(scoreboard)

    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template(
        '404.html',
        **extract_session_objs('404')
    ), 404


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)
