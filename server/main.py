import base64
import hashlib
import json
import logging
import os
from datetime import timedelta

from werkzeug.middleware.profiler import ProfilerMiddleware
import cuwais.database
from flask import Flask, render_template, request, abort, Response, redirect
from flask_session import Session

from server import login, data, nav, repo, caching
from server.caching import cached

app = Flask(
    __name__,
    template_folder="templates",
)
with open("/run/secrets/secret_key") as secrets_file:
    secret = "".join(secrets_file.readlines())
    app.secret_key = secret
    app.config["SECRET_KEY"] = secret
app.config["DEBUG"] = os.getenv('DEBUG') == 'True'

if app.config["DEBUG"]:
    app.config['PROFILE'] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])


app.config["SESSION_COOKIE_NAME"] = "cuwais_session"
app.config["SERVER_NAME"] = str(os.getenv('SERVER_NAME'))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)
app.config["SESSION_TYPE"] = 'redis'
app.config["SESSION_REDIS"] = caching.redis_connection
sess = Session(app)

logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.WARNING)


class HTMLError(RuntimeError):
    def __init__(self, page, code):
        super(HTMLError, self).__init__(f"Error {code}")
        self.page = page
        self.code = code

    def make_response(self):
        return self.page, self.code


def expose_root_file(file_name):
    file_path = "root/" + file_name

    def new_endpoint():
        return app.send_static_file(file_path)
    new_endpoint.__name__ = name
    app.route('/' + name)(new_endpoint)


# Favicons
root_path = os.path.join(app.root_path, "static/root")
for name in [f for f in os.listdir(root_path) if os.path.isfile(os.path.join(root_path, f))]:
    expose_root_file(name)


def session_bound(f):
    def f_new(*args, **kwargs):
        try:
            with cuwais.database.create_session() as s:
                result = f(*args, db_session=s, **kwargs)
                s.commit()
            return result
        except HTMLError as e:
            return e.make_response()

    f_new.__name__ = f.__name__
    return f_new


def logged_in_session_bound(f):
    @session_bound
    def f_new(db_session, *args, **kwargs):
        user = data.get_user(db_session)
        if user is None:
            raise HTMLError(render_template(
                'login-required.html',
                **nav.extract_session_objs(None, 'login-required'),
            ), 403)
        return f(*args, db_session=db_session, user=user, **kwargs)

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


def admin_session_bound(f):
    @logged_in_session_bound
    def f_new(user: cuwais.database.User, db_session, *args, **kwargs):
        if not user.is_admin:
            raise HTMLError(render_template(
                '404.html',
                **nav.extract_session_objs(user, '404')
            ), 404)
        return f(*args, db_session=db_session, user=user, **kwargs)

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


@cached(ttl=0 if app.config["DEBUG"] else 600)
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


def reason_crash(reason):
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
    return names.get(reason, "I'm not sure what this means, so is probably a bug. Sorry!")


app.jinja_env.globals['reason_crash'] = reason_crash


@app.route('/')
def index(db_session):
    user = data.get_user(db_session)
    if user is not None:
        return redirect('/leaderboard')
    return redirect('/about')


@app.route('/about')
@session_bound
def about(db_session):
    return render_template(
        'about.html',
        **nav.extract_session_objs(data.get_user(db_session), 'about')
    )


@app.route('/leaderboard')
@logged_in_session_bound
def leaderboard(user, db_session):
    scoreboard = data.get_scoreboard(db_session, user)
    return render_template(
        'leaderboard.html',
        leaderboard=scoreboard,
        **nav.extract_session_objs(user, 'leaderboard')
    )


@app.route('/submissions')
@logged_in_session_bound
def submissions(user, db_session):
    subs = data.get_all_user_submissions(db_session, user, private=True)
    current_sub = data.get_current_submission(db_session, user)
    return render_template(
        'submissions.html',
        submissions=subs,
        current_sub_id=current_sub.id if current_sub is not None else None,
        **nav.extract_session_objs(user, 'submissions')
    )


@app.route('/me')
@logged_in_session_bound
def me(user, db_session):
    return render_template(
        'me.html',
        **nav.extract_session_objs(user, 'me')
    )


@app.route('/admin')
@admin_session_bound
def admin(user, db_session):
    return render_template(
        'admin.html',
        **nav.extract_session_objs(user, 'admin')
    )


@app.route('/bots')
@admin_session_bound
def bots(user, db_session):
    bot_subs = data.get_all_bot_submissions(db_session)
    bot_subs = [{"id": bot.id, "name": bot.display_name, "date": sub.submission_date} for bot, sub in bot_subs]
    return render_template(
        'bots.html',
        bots=bot_subs,
        **nav.extract_session_objs(user, 'bots')
    )


@app.route('/logout')
def logout():
    data.remove_user()

    return render_template(
        'logout.html',
        **nav.extract_session_objs(None, 'logout')
    )


@app.route('/enable-js')
def please_enable_js():
    return render_template(
        'please_enable_js.html',
        **nav.extract_session_objs(None, 'please_enable_js')
    )


@app.route('/api/login_google', methods=['POST'])
@session_bound
def login_google(db_session):
    json_in = request.get_json()
    if 'idtoken' not in json_in:
        abort(400)
    token = json_in.get('idtoken')

    user = login.get_user_from_google_token(db_session, token)
    data.save_user_id(user.id)

    return Response(json.dumps(user.to_private_dict()),
                    status=200,
                    mimetype='application/json')


def _make_api_failure(message):
    encoded = json.dumps({"status": "fail", "message": message})
    return Response(encoded,
                    status=400,
                    mimetype='application/json')


@app.route('/api/add_submission', methods=['POST'])
@logged_in_session_bound
def add_submission(user, db_session):
    json_in = request.json
    url = json_in["url"]
    try:
        submission_id = data.create_submission(db_session, user, url)
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
@admin_session_bound
def add_bot(user, db_session):
    json_in = request.json
    url = json_in["url"]
    bot_name = json_in["name"]
    try:
        bot_id = data.create_bot(db_session, bot_name)
        submission_id = data.create_submission(db_session, bot_id, url)
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


@app.route('/api/set_name_visible', methods=['POST'])
@logged_in_session_bound
def set_name_visible(user, db_session):
    json_in = request.json
    should_be_visible = json_in["visible"]

    data.set_user_name_visible(db_session, user, should_be_visible)

    encoded = json.dumps({"status": "success"})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/remove_bot', methods=['POST'])
@admin_session_bound
def remove_bot(user, db_session):
    json_in = request.json
    bot_id = json_in["id"]
    data.delete_bot(db_session, bot_id)

    encoded = json.dumps({"status": "success"})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/set_submission_active', methods=['POST'])
@logged_in_session_bound
def set_submission_active(user, db_session):
    json_in = request.json
    submission_id = json_in["submission_id"]
    enabled = json_in["enabled"]

    if not data.submission_is_owned_by_user(db_session, submission_id, user.id):
        return _make_api_failure("You do not own that submission!")

    data.set_submission_enabled(db_session, submission_id, enabled)

    encoded = json.dumps({"status": "success", "submission_id": submission_id})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_leaderboard_over_time', methods=['POST'])
@logged_in_session_bound
def get_leaderboard_over_time(user, db_session):
    graph = data.get_leaderboard_graph(db_session, user.id)

    encoded = json.dumps({"status": "success", "data": graph})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_submission_summary_graph', methods=['POST'])
@logged_in_session_bound
def get_submission_summary_graph(user, db_session):
    json_in = request.json
    submission_id = json_in["submission_id"]

    if not data.submission_is_owned_by_user(db_session, submission_id, user.id):
        return _make_api_failure("You do not own that submission!")

    summary_data = data.get_submission_summary_data(submission_id)

    encoded = json.dumps(summary_data)
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.errorhandler(404)
def page_404(e):
    return render_template(
        '404.html',
        **nav.extract_session_objs(None, '404')
    ), 404


if __name__ == "__main__":
    cuwais.database.create_tables()
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)
