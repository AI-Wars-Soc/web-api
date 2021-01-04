import logging
import os
from datetime import timedelta

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


def get_user():
    cuwais_user = cuwais.common.decode(session.get("cuwais_user", "null"))
    return cuwais_user


def remove_user():
    session.pop("cuwais_user", None)


def extract_session_objs():
    return dict(
        user=get_user()
    )


def ensure_logged_in(f):
    def f_new():
        user = get_user()
        if user is None:
            return redirect('/')
        return f()
    return f_new


@app.route('/')
def index():
    user = get_user()
    if user is not None:
        return redirect('/home')
    return render_template(
        'index.html',
        **extract_session_objs()
    )


@app.route('/home')
@ensure_logged_in
def home():
    return render_template(
        'index.html',
        **extract_session_objs()
    )


@app.route('/login_google', methods=['POST'])
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


@app.route('/logout')
def logout():
    remove_user()

    return render_template(
        'logout.html',
        **extract_session_objs()
    )


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=8080)
