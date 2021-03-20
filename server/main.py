import base64
import hashlib
import json
import logging
import os
from datetime import timedelta

import cuwais
import redis
from cuwais.database import User
from flask import Flask, render_template, request, abort, Response, redirect
from flask_session import Session

from server import login, data, nav, repo

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


def ensure_logged_in(f):
    def f_new():
        user_id = data.get_user_id()
        if user_id is None:
            return render_template(
                'login-required.html',
                **nav.extract_session_objs('login-required')
            )
        return f(user_id)

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


def generate_sri(inp_file):
    hashed = hashlib.sha256()

    file = os.path.join(os.path.dirname(os.path.abspath(__file__)), inp_file[1:])
    print(file, flush=True)
    with open(file, 'rb') as f:
        while True:
            vs = f.read(65536)
            if not vs:
                break
            hashed.update(vs)
    hashed = hashed.digest()
    hash_base64 = base64.b64encode(hashed).decode('utf-8')
    return 'sha256-{}'.format(hash_base64)


app.jinja_env.globals['sri'] = generate_sri


@app.route('/')
def index():
    user = data.get_user_id()
    if user is not None:
        return redirect('/leaderboard')
    return redirect('/about')


@app.route('/about')
def about():
    return render_template(
        'about.html',
        **nav.extract_session_objs('about')
    )


@app.route('/leaderboard')
@ensure_logged_in
def leaderboard(user_id):
    return render_template(
        'leaderboard.html',
        **nav.extract_session_objs('leaderboard')
    )


@app.route('/submissions')
@ensure_logged_in
def submissions(user_id):
    with cuwais.database.create_session() as database_session:
        subs = data.get_all_user_submissions(database_session, user_id, private=True)
        return render_template(
            'submissions.html',
            submissions=subs,
            **nav.extract_session_objs('submissions', database_session)
        )


@app.route('/me')
@ensure_logged_in
def me(user_id):
    return render_template(
        'me.html',
        **nav.extract_session_objs('me')
    )


@app.route('/logout')
def logout():
    data.remove_user()

    return render_template(
        'logout.html',
        **nav.extract_session_objs('logout')
    )


@app.route('/enable-js')
def please_enable_js():
    return render_template(
        'please_enable_js.html',
        **nav.extract_session_objs('please_enable_js')
    )


@app.route('/api/login_google', methods=['POST'])
def login_google():
    json_in = request.get_json()
    if 'idtoken' not in json_in:
        abort(400)
    token = json_in.get('idtoken')

    user_id = login.get_user_id_from_google_token(token)
    data.save_user_id(user_id)

    response = {}
    with cuwais.database.create_session() as database_session:
        user = data.get_user_from_id(database_session, user_id)
        response["user_id"] = user.id
        response["user_name"] = user.display_name

    return Response(json.dumps(response),
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_leaderboard')
@ensure_logged_in
def get_leaderboard(user_id):
    scoreboard = data.get_scoreboard()

    return Response(json.dumps(scoreboard),
                    status=200,
                    mimetype='application/json')


def _make_submission_failure(message):
        encoded = json.dumps({"status": "fail", "message": message})
        return Response(encoded,
                        status=400,
                        mimetype='application/json')


@app.route('/api/add_submission', methods=['POST'])
@ensure_logged_in
def add_submission(user_id):
    json_in = request.json
    url = json_in["url"]
    try:
        submission_id = data.create_submission(user_id, url)
    except repo.InvalidGitURL:
        return _make_submission_failure("Invalid GIT URL")
    except repo.AlreadyExistsException:
        return _make_submission_failure("GIT repo already submitted")
    except repo.RepoTooBigException:
        return _make_submission_failure("GIT repo is too large!")

    encoded = json.dumps({"status": "success", "submission_id": submission_id})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/set_submission_active', methods=['POST'])
@ensure_logged_in
def set_submission_active(user_id):
    json_in = request.json
    submission_id = json_in["submission_id"]
    enabled = json_in["enabled"]

    print(user_id, submission_id, enabled, flush=True)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template(
        '404.html',
        **nav.extract_session_objs('404')
    ), 404


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)
