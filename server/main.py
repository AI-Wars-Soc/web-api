import logging
import os

from google.auth import exceptions
from google.oauth2 import id_token
import google.auth.transport.requests
import cachecontrol
import requests

from flask import Flask, render_template, request, abort

app = Flask(
    __name__,
    template_folder="templates"
)
with open("/run/secrets/secret_key") as f:
    app.secret_key = f.readlines()
app.config["DEBUG"] = os.getenv('DEBUG') == 'True'

logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.WARNING)

session = requests.session()
cached_session = cachecontrol.CacheControl(session)

CLIENT_ID = "389788965612-qh4j3n7fh14nfjbg7u1tmlb59mudmobj.apps.googleusercontent.com"


@app.route('/')
def index():
    return render_template(
        'index.html',
        light_mode=True,
        user=None
    )


@app.route('/login_google', methods=['POST'])
def login_google():
    json = request.get_json()
    if 'idtoken' not in json:
        abort(400)
    token = json.get('idtoken')
    id_info = None
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        google_request = google.auth.transport.requests.Request(session=cached_session)
        id_info = id_token.verify_oauth2_token(token, google_request, CLIENT_ID)

        if id_info['iss'] != 'https://accounts.google.com':
            raise ValueError('Wrong issuer.')

    except exceptions.GoogleAuthError:
        logging.warning("Attempted login with invalid token: " + token)
        abort(400)
    except ValueError:
        abort(400)
    return id_info


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=8080)
