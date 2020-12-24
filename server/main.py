import logging
import os

from flask import Flask, render_template


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
        'index.html'
    )


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="0.0.0.0", port=80)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=80)
