import logging
from datetime import timedelta

import cuwais.database
from cuwais.config import config_file
from fastapi import FastAPI, HTTPException
from fastapi_utils.timing import add_timing_middleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app import login, data, nav, repo, caching, subrunner

app = FastAPI()
# app.mount("/", StaticFiles(directory="/home/web_user/app/static"), name="static")

config = dict()

templates = Jinja2Templates(directory="templates")

with open("/run/secrets/secret_key") as secrets_file:
    secret = "".join(secrets_file.readlines())
    config["SECRET_KEY"] = secret
config["DEBUG"] = config_file.get("debug")

if config["DEBUG"]:
    config['PROFILE'] = config_file.get("profile")
    if config['PROFILE']:
        add_timing_middleware(app, record=logging.info, prefix="app", exclude="untimed")

config["SESSION_COOKIE_NAME"] = "session_id"
config["SESSION_PERMANENT"] = False
config["SESSION_COOKIE_SECURE"] = not config["DEBUG"]
config["SERVER_NAME"] = config_file.get("front_end.server_name")
config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
config["SESSION_TYPE"] = 'redis'
config["SESSION_REDIS"] = caching.redis_connection

logging.basicConfig(level=logging.DEBUG if config["DEBUG"] else logging.WARNING)


def rich_render_template(page_name, user, **kwargs):
    return templates.TemplateResponse(page_name + '.html',
                                      {
                                          page_name: page_name,
                                          config_file: config_file.get_all(),
                                          **nav.extract_session_objs(user, page_name),
                                          **kwargs
                                      }
                                      )


def abort404():
    raise HTTPException(status_code=404, detail="Item not found")


def abort400():
    raise HTTPException(status_code=400, detail="Invalid request")


def session_bound(f):
    async def f_new(request: Request, *args, **kwargs):
        with cuwais.database.create_session() as s:
            result = await f(request, *args, db_session=s, **kwargs)
            s.commit()
        return result

    f_new.__name__ = f.__name__
    return f_new


def logged_in_session_bound(f):
    @session_bound
    async def f_new(request: Request, db_session, *args, **kwargs):
        user = data.get_user(db_session)
        if user is None:
            return rich_render_template(
                'login-required', None
            )
        return await f(request, *args, db_session=db_session, user=user, **kwargs)

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


def admin_session_bound(f):
    @logged_in_session_bound
    async def f_new(request: Request, user: cuwais.database.User, db_session, *args, **kwargs):
        if not user.is_admin:
            abort404()
        return await f(request, *args, db_session=db_session, user=user, **kwargs)

    # Renaming the function name to appease flask
    f_new.__name__ = f.__name__
    return f_new


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


templates.env.globals['human_format'] = human_format


def reason_crash(reason):
    crash_reasons = config_file.get("localisation.crash_reasons")
    default_crash_reason = config_file.get("localisation.default_crash_reason")
    return crash_reasons.get(reason, default_crash_reason)


@app.get('/', response_class=HTMLResponse)
@session_bound
async def index(request: Request, db_session):
    user = data.get_user(db_session)
    if user is not None:
        return RedirectResponse('/leaderboard')
    return RedirectResponse('/about')


@app.get('/about', response_class=HTMLResponse)
@session_bound
async def about(request: Request, db_session):
    return rich_render_template(
        'about', data.get_user(db_session)
    )


@app.get('/leaderboard', response_class=HTMLResponse)
@logged_in_session_bound
async def leaderboard(request: Request, user, db_session):
    return rich_render_template(
        'leaderboard', user
    )


@app.get('/submissions', response_class=HTMLResponse)
@logged_in_session_bound
async def submissions(request: Request, user, db_session):
    return rich_render_template(
        'submissions', user
    )


def validate_submission_viewable(db_session, user, submission_id):
    return data.is_current_submission(db_session, submission_id) \
           or data.submission_is_owned_by_user(db_session, submission_id, user)


def validate_submission_playable(db_session, user, submission_id):
    return validate_submission_viewable(db_session, user, submission_id) \
           and data.is_submission_healthy(db_session, submission_id)


@app.get('/play/<submission_id>', response_class=HTMLResponse)
@logged_in_session_bound
async def play(request: Request, user, db_session, submission_id):
    if not validate_submission_playable(db_session, user, submission_id):
        abort404()

    game_boards = {"chess": 'games/game_chess'}
    game = config_file.get("gamemode.id")
    if game not in game_boards.keys():
        return game

    return rich_render_template(
        game_boards[game], user
    )


@app.get('/me', response_class=HTMLResponse)
@logged_in_session_bound
async def me(request: Request, user, db_session):
    return rich_render_template(
        'me', user
    )


@app.get('/admin', response_class=HTMLResponse)
@admin_session_bound
async def admin(request: Request, user, db_session):
    return rich_render_template(
        'admin', user
    )


@app.get('/bots', response_class=HTMLResponse)
@admin_session_bound
async def bots(request: Request, user, db_session):
    bot_subs = data.get_all_bot_submissions(db_session)
    bot_subs = [{"id": bot.id, "name": bot.display_name, "date": sub.submission_date} for bot, sub in bot_subs]
    return rich_render_template(
        'bots', user, bots=bot_subs
    )


@app.get('/logout', response_class=HTMLResponse)
async def logout(request: Request):
    data.remove_user()

    return rich_render_template(
        'logout', None
    )


@app.get('/enable-js', response_class=HTMLResponse)
async def please_enable_js(request: Request):
    return rich_render_template(
        'please_enable_js', None
    )


@app.post('/api/login_google', response_class=JSONResponse)
@session_bound
async def login_google(request: Request, db_session):
    json_in = await request.json()
    if 'idtoken' not in json_in:
        abort400()
    token = json_in.get('idtoken')

    user = login.get_user_from_google_token(db_session, token)
    data.save_user_id(user.id)

    return user.to_private_dict()


@app.post('/api/play/<submission_id>/connect', response_class=JSONResponse)
@logged_in_session_bound
async def play_get_move(request: Request, user, db_session, submission_id):
    if not validate_submission_playable(db_session, user, submission_id):
        abort404()

    json_in = await request.json()
    if 'board' not in json_in:
        abort400()
    if 'move' not in json_in:
        abort400()
    board = json_in.get('board')
    move = json_in.get('move')

    next_board = subrunner.get_next_board(board, move)

    return next_board


def _make_api_failure(message):
    return {"status": "fail", "message": message}


@app.post('/api/add_submission', response_class=JSONResponse)
@logged_in_session_bound
async def add_submission(request: Request, user, db_session):
    json_in = await request.json()
    if 'url' not in json_in:
        abort400()
    url = json_in.get('url')
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
        return {"status": "resent"}

    return {"status": "success", "submission_id": submission_id}


@app.post('/api/add_bot', response_class=JSONResponse)
@admin_session_bound
async def add_bot(request: Request, user, db_session):
    json_in = await request.json()
    if 'url' not in json_in:
        abort400()
    url = json_in.get('url')
    if 'name' not in json_in:
        abort400()
    bot_name = json_in.get('name')
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

    return {"status": "success", "submission_id": submission_id}


@app.post('/api/set_name_visible', response_class=JSONResponse)
@logged_in_session_bound
async def set_name_visible(request: Request, user, db_session):
    json_in = await request.json()
    if 'visible' not in json_in:
        abort400()
    should_be_visible = json_in.get('visible')

    data.set_user_name_visible(db_session, user, should_be_visible)

    return {"status": "success"}


@app.post('/api/remove_bot', response_class=JSONResponse)
@admin_session_bound
async def remove_bot(request: Request, user, db_session):
    json_in = await request.json()
    if 'id' not in json_in:
        abort400()
    bot_id = json_in.get('id')
    data.delete_bot(db_session, bot_id)

    return {"status": "success"}


@app.post('/api/remove_user', response_class=JSONResponse)
@logged_in_session_bound
async def remove_user(request: Request, user, db_session):
    data.delete_user(db_session, user)

    return {"status": "success"}


@app.post('/api/set_submission_active', response_class=JSONResponse)
@logged_in_session_bound
async def set_submission_active(request: Request, user, db_session):
    json_in = await request.json()
    if 'submission_id' not in json_in:
        abort400()
    submission_id = json_in.get('submission_id')
    if 'enabled' not in json_in:
        abort400()
    enabled = json_in.get('enabled')

    if not data.submission_is_owned_by_user(db_session, submission_id, user.id):
        return _make_api_failure(config_file.get("localisation.submission_access_error"))

    data.set_submission_enabled(db_session, submission_id, enabled)

    return {"status": "success", "submission_id": submission_id}


@app.post('/api/get_leaderboard', response_class=JSONResponse)
@logged_in_session_bound
async def get_leaderboard_data(request: Request, user, db_session):
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

    return {"entries": transformed}


@app.post('/api/get_submissions', response_class=JSONResponse)
@logged_in_session_bound
async def get_submissions_data(request: Request, user, db_session):
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

    return {"submissions": transformed_subs, "no_submissions": len(transformed_subs) == 0}


@app.post('/api/get_leaderboard_over_time', response_class=JSONResponse)
@logged_in_session_bound
async def get_leaderboard_over_time(request: Request, user, db_session):
    graph = data.get_leaderboard_graph(db_session, user.id)

    return {"status": "success", "data": graph}


@app.post('/api/get_submission_summary_graph', response_class=JSONResponse)
@logged_in_session_bound
async def get_submission_summary_graph(request: Request, user, db_session):
    json_in = await request.json()
    if 'submission_id' not in json_in:
        abort400()
    submission_id = json_in.get('submission_id')

    if not data.submission_is_owned_by_user(db_session, submission_id, user.id):
        return _make_api_failure(config_file.get("localisation.submission_access_error"))

    summary_data = data.get_submission_summary_data(submission_id)

    return summary_data
