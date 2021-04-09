import base64
import hashlib
import json
import logging
import os
from datetime import timedelta

import cuwais
import cuwais.database
from flask import Flask, render_template, request, abort, Response, redirect
from flask_session import Session

from server import login, data, nav, repo, caching

app = Flask(
    __name__,
    template_folder="templates"
)
with open("/run/secrets/secret_key") as secrets_file:
    secret = "".join(secrets_file.readlines())
    app.secret_key = secret
    app.config["SECRET_KEY"] = secret
app.config["DEBUG"] = os.getenv('DEBUG') == 'True'

app.config["SESSION_COOKIE_NAME"] = "cuwais_session"
app.config["SERVER_NAME"] = str(os.getenv('SERVER_NAME'))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)
app.config["SESSION_TYPE"] = 'redis'
app.config["SESSION_REDIS"] = caching.redis_connection
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


def ensure_admin(f):
    @ensure_logged_in
    def f_new(user_id):
        user = data.get_user_from_id(user_id)
        if user is None or not user.is_admin:
            return page_not_found()
        return f(user)

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


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


app.jinja_env.globals['human_format'] = human_format


def reason_crash(name):
    names = {"illegal-move": "This means your AI returned a move which was not allowed",
             "illegal-board": "This means there was a mismatch between the host and client boards. "
                              "This means either you've intentionally tried to break something, or there's a bug",
             "broken-entry-point": "This means your repository did not have the right method to call! "
                                   "Make sure you have all of the same file and method names as the base repository",
             "unknown-result-type": "This is definitely a bug. Please let someone know",
             "game-unfinished": "This means your AI stopped playing the game before the game was done. "
                                "This usually means your AI somehow crashed, but probably not by timing out",
             "timeout": "This means your AI ran out of time. Try making moves faster!",
             "process-killed": "This means your AI used up too much of the system's resources. "
                               "Usually this means you used too much memory"}
    return names.get(name, "I'm not sure what this means, so is probably a bug. Sorry!")


app.jinja_env.globals['reason_crash'] = reason_crash


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
    scoreboard = data.get_scoreboard(user_id)
    return render_template(
        'leaderboard.html',
        leaderboard=scoreboard,
        **nav.extract_session_objs('leaderboard')
    )


@app.route('/submissions')
@ensure_logged_in
def submissions(user_id):
    subs = data.get_all_user_submissions(user_id, private=True)
    current_sub = data.get_current_submission(user_id)
    return render_template(
        'submissions.html',
        submissions=subs,
        current_sub_id=current_sub.id if current_sub is not None else None,
        **nav.extract_session_objs('submissions')
    )


@app.route('/me')
@ensure_logged_in
def me(user_id):
    return render_template(
        'me.html',
        **nav.extract_session_objs('me')
    )


@app.route('/admin')
@ensure_admin
def admin(user):
    return render_template(
        'admin.html',
        **nav.extract_session_objs('admin')
    )


@app.route('/bots')
@ensure_admin
def bots(user):
    bot_subs = data.get_all_bot_submissions()
    bot_subs = [{"id": bot.id, "name": bot.display_name, "date": sub.submission_date} for bot, sub in bot_subs]
    return render_template(
        'bots.html',
        bots=bot_subs,
        **nav.extract_session_objs('bots')
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

    response = dict()
    user = data.get_user_from_id(user_id)
    response["user_id"] = user.id
    response["user_name"] = user.display_name

    return Response(json.dumps(response),
                    status=200,
                    mimetype='application/json')


def _make_api_failure(message):
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
        return _make_api_failure("Invalid GIT URL")
    except repo.AlreadyExistsException:
        return _make_api_failure("GIT repo already submitted")
    except repo.RepoTooBigException:
        return _make_api_failure("GIT repo is too large!")
    except repo.CantCloneException:
        return _make_api_failure("Failed to clone! :(")
    except repo.AlreadyCloningException:
        encoded = json.dumps({"status": "resent"})
        return Response(encoded,
                        status=200,
                        mimetype='application/json')

    encoded = json.dumps({"status": "success", "submission_id": submission_id})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/add_bot', methods=['POST'])
@ensure_admin
def add_bot(user):
    json_in = request.json
    url = json_in["url"]
    name = json_in["name"]
    try:
        bot_id = data.create_bot(name)
        submission_id = data.create_submission(bot_id, url)
    except repo.InvalidGitURL:
        return _make_api_failure("Invalid GIT URL")
    except repo.AlreadyExistsException:
        return _make_api_failure("GIT repo already submitted")
    except repo.RepoTooBigException:
        return _make_api_failure("GIT repo is too large!")
    except repo.CantCloneException:
        return _make_api_failure("Failed to clone! :(")

    encoded = json.dumps({"status": "success", "submission_id": submission_id})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/remove_bot', methods=['POST'])
@ensure_admin
def remove_bot(user):
    json_in = request.json
    bot_id = json_in["id"]
    data.delete_bot(bot_id)

    encoded = json.dumps({"status": "success"})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/set_submission_active', methods=['POST'])
@ensure_logged_in
def set_submission_active(user_id):
    json_in = request.json
    submission_id = json_in["submission_id"]
    enabled = json_in["enabled"]

    if not data.submission_is_owned_by_user(submission_id, user_id):
        return _make_api_failure("You do not own that submission!")

    data.set_submission_enabled(submission_id, enabled)

    encoded = json.dumps({"status": "success", "submission_id": submission_id})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_leaderboard_over_time', methods=['POST'])
@ensure_logged_in
def get_leaderboard_over_time(user_id):
    graph = data.get_leaderboard_graph(user_id)

    encoded = json.dumps({"status": "success", "data": graph})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_submission_summary_graph', methods=['POST'])
@ensure_logged_in
def get_submission_summary_graph(user_id):
    json_in = request.json
    submission_id = json_in["submission_id"]

    if not data.submission_is_owned_by_user(submission_id, user_id):
        return _make_api_failure("You do not own that submission!")

    summary_data = data.get_submission_summary_data(submission_id)

    encoded = json.dumps(summary_data)
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.errorhandler(404)
def page_404(e):
    return page_not_found()


def page_not_found():
    # note that we set the 404 status explicitly
    return render_template(
        '404.html',
        **nav.extract_session_objs('404')
    ), 404


if __name__ == "__main__":
    cuwais.database.create_tables()
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)
