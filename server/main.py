import base64
import hashlib
import json
import logging
import os
from datetime import timedelta

from jinja2 import Markup
from werkzeug.middleware.profiler import ProfilerMiddleware
import cuwais.database
from cuwais.config import config_file
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
app.config["DEBUG"] = config_file.get("debug")

if app.config["DEBUG"]:
    app.config['PROFILE'] = config_file.get("profile")
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

app.config["SESSION_COOKIE_NAME"] = "session_id"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_SECURE"] = not app.config["DEBUG"]
app.config["SERVER_NAME"] = config_file.get("front_end.server_name")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
app.config["SESSION_TYPE"] = 'redis'
app.config["SESSION_REDIS"] = caching.redis_connection
sess = Session(app)

logging.basicConfig(level=logging.DEBUG if app.config["DEBUG"] else logging.WARNING)


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


def rich_render_template(page_name, user, **kwargs):
    return render_template(
        page_name + '.html',
        page_name=page_name,
        config_file=config_file.get_all(),
        **nav.extract_session_objs(user, page_name),
        **kwargs
    )


def session_bound(f):
    def f_new(*args, **kwargs):
        with cuwais.database.create_session() as s:
            result = f(*args, db_session=s, **kwargs)
            s.commit()
        return result

    f_new.__name__ = f.__name__
    return f_new


def logged_in_session_bound(f):
    @session_bound
    def f_new(db_session, *args, **kwargs):
        user = data.get_user(db_session)
        if user is None:
            abort(Response(rich_render_template(
                'login-required', None
            )))
        return f(*args, db_session=db_session, user=user, **kwargs)

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


def admin_session_bound(f):
    @logged_in_session_bound
    def f_new(user: cuwais.database.User, db_session, *args, **kwargs):
        if not user.is_admin:
            abort(404)
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
    crash_reasons = config_file.get("localisation.crash_reasons")
    default_crash_reason = config_file.get("localisation.default_crash_reason")
    return crash_reasons.get(reason, default_crash_reason)


app.jinja_env.globals['reason_crash'] = reason_crash


@app.route('/')
@session_bound
def index(db_session):
    user = data.get_user(db_session)
    if user is not None:
        return redirect('/leaderboard')
    return redirect('/about')


@app.route('/about')
@session_bound
def about(db_session):
    return rich_render_template(
        'about', data.get_user(db_session)
    )


@app.route('/leaderboard')
@logged_in_session_bound
def leaderboard(user, db_session):
    return rich_render_template(
        'leaderboard', user
    )


@app.route('/submissions')
@logged_in_session_bound
def submissions(user, db_session):
    return rich_render_template(
        'submissions', user
    )


def validate_submission_viewable(db_session, user, submission_id):
    return data.is_current_submission(db_session, submission_id) \
           or data.submission_is_owned_by_user(db_session, submission_id, user)


def validate_submission_playable(db_session, user, submission_id):
    return validate_submission_viewable(db_session, user, submission_id) \
            and data.is_submission_healthy(db_session, submission_id)


@app.route('/play/<submission_id>')
@logged_in_session_bound
def play(user, db_session, submission_id):
    if not validate_submission_playable(db_session, user, submission_id):
        abort(404)

    game_boards = {"chess": 'games/game_chess'}
    game = config_file.get("gamemode.id")
    if game not in game_boards.keys():
        return game

    return rich_render_template(
        game_boards[game], user
    )


@app.route('/me')
@logged_in_session_bound
def me(user, db_session):
    return rich_render_template(
        'me', user
    )


@app.route('/admin')
@admin_session_bound
def admin(user, db_session):
    return rich_render_template(
        'admin', user
    )


@app.route('/bots')
@admin_session_bound
def bots(user, db_session):
    bot_subs = data.get_all_bot_submissions(db_session)
    bot_subs = [{"id": bot.id, "name": bot.display_name, "date": sub.submission_date} for bot, sub in bot_subs]
    return rich_render_template(
        'bots', user, bots=bot_subs
    )


@app.route('/logout')
def logout():
    data.remove_user()

    return rich_render_template(
        'logout', None
    )


@app.route('/enable-js')
def please_enable_js():
    return rich_render_template(
        'please_enable_js', None
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
        return _make_api_failure(config_file.get("localisation.git_errors.invalid-url"))
    except repo.AlreadyExistsException:
        return _make_api_failure(config_file.get("localisation.git_errors.already-submitted"))
    except repo.RepoTooBigException:
        return _make_api_failure(config_file.get("localisation.git_errors.too-large"))
    except repo.CantCloneException:
        return _make_api_failure(config_file.get("localisation.git_errors.clone-fail"))
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
    bot = data.create_bot(db_session, bot_name)
    db_session.commit()  # TODO: Make this atomic
    try:
        submission_id = data.create_submission(db_session, bot, url)
    except repo.InvalidGitURL:
        return _make_api_failure(config_file.get("localisation.git_errors.invalid-url"))
    except repo.AlreadyExistsException:
        return _make_api_failure(config_file.get("localisation.git_errors.already-submitted"))
    except repo.RepoTooBigException:
        return _make_api_failure(config_file.get("localisation.git_errors.too-large"))
    except repo.CantCloneException:
        return _make_api_failure(config_file.get("localisation.git_errors.clone-fail"))

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


@app.route('/api/remove_user', methods=['POST'])
@logged_in_session_bound
def remove_user(user, db_session):
    data.delete_user(db_session, user)

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
        return _make_api_failure(config_file.get("localisation.submission_access_error"))

    data.set_submission_enabled(db_session, submission_id, enabled)

    encoded = json.dumps({"status": "success", "submission_id": submission_id})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_leaderboard', methods=['POST'])
@logged_in_session_bound
def get_leaderboard_data(user, db_session):
    scoreboard = data.get_scoreboard(db_session, user)

    def transform(item, i):
        trans = {"position": i,
                 "name": item["user"]["display_name"],
                 "is_real_name": item["user"]["display_real_name"],
                 "nickname": item["user"]["nickname"],
                 "wins": item["outcomes"]["wins"],
                 "losses": item["outcomes"]["losses"],
                 "draws": item["outcomes"]["draws"],
                 "score": item["score_text"],
                 "boarder_style": "leaderboard-user-submission" if item["is_you"]
                 else "leaderboard-bot-submission" if item["is_bot"]
                 else "leaderboard-other-submission"}

        return trans

    transformed = [transform(sub, i + 1) for i, sub in enumerate(scoreboard)]

    encoded = json.dumps({"entries": transformed})
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.route('/api/get_submissions', methods=['POST'])
@logged_in_session_bound
def get_submissions_data(user, db_session):
    subs = data.get_all_user_submissions(db_session, user, private=True)
    current_sub = data.get_current_submission(db_session, user)

    def transform(sub, i):
        selected = current_sub is not None and sub['submission_id'] == current_sub.id

        class_names = []
        if sub['active']:
            class_names.append('submission-entry-active')
        if sub['tested'] and not sub['healthy']:
            class_names.append('invalid-stripes')
        if not sub['tested']:
            class_names.append('testing-stripes')
        if selected:
            class_names.append('submission-entry-selected')

        trans = {"div_class": " ".join(class_names),
                 "subdiv_class":
                     'submission-entry-testing' if not sub['tested']
                     else 'submission-entry-invalid' if not sub['healthy']
                     else "",
                 "index": i,
                 "submission_id": sub["submission_id"],
                 "submission_date": sub["submission_date"].strftime('%d %b at %I:%M %p'),
                 "active": sub['active'],
                 "healthy": sub['healthy'],
                 "crashed": sub['tested'] and not sub['healthy'],
                 "status": "Selected" if selected
                 else "Testing" if not sub['tested']
                 else "Invalid" if not sub['healthy']
                 else "",
                 "enabled_status": "Enabled" if sub['active'] else "Disabled",
                 }

        crash = sub['crash']
        if crash is not None:
            trans = {**trans,
                     "crash_reason": crash['result'].replace("-", " ").capitalize(),
                     "crash_reason_long": reason_crash(crash['result']),
                     "no_print": len(crash['prints']) == 0,
                     "prints": crash['prints']}

        return trans

    transformed_subs = [transform(sub, len(subs) - i)
                        for i, sub in enumerate(subs)]

    encoded = json.dumps({"submissions": transformed_subs, "no_submissions": len(transformed_subs) == 0})
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
        return _make_api_failure(config_file.get("localisation.submission_access_error"))

    summary_data = data.get_submission_summary_data(submission_id)

    encoded = json.dumps(summary_data)
    return Response(encoded,
                    status=200,
                    mimetype='application/json')


@app.errorhandler(404)
def page_404(e):
    return rich_render_template(
        '404', None
    ), 404


if __name__ == "__main__":
    cuwais.database.create_tables()
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)
