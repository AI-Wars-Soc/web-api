import logging
import os

import cuwais.common
from flask import Flask, render_template, request, abort, Response

from server import login

app = Flask(
    __name__,
    template_folder="templates"
)
with open("/run/secrets/secret_key") as f:
    app.secret_key = f.readlines()
app.config["DEBUG"] = os.getenv('DEBUG') == 'True'

logging.basicConfig(level=logging.DEBUG if os.getenv('DEBUG') else logging.WARNING)


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

    user = login.get_user_from_google_token(token)

    return Response(cuwais.common.encode(user),
                    status=200,
                    mimetype='application/json')


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=8080)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=8080)
