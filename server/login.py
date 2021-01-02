import logging

from google.auth import exceptions
from google.oauth2 import id_token
import google.auth.transport.requests
import cachecontrol
import requests

from werkzeug.exceptions import abort
from cuwais.common import User

session = requests.session()
cached_session = cachecontrol.CacheControl(session)

CLIENT_ID = "389788965612-qh4j3n7fh14nfjbg7u1tmlb59mudmobj.apps.googleusercontent.com"


def get_user_from_google_token(token) -> User:
    id_info = None
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        google_request = google.auth.transport.requests.Request(session=cached_session)
        id_info = id_token.verify_oauth2_token(token, google_request, CLIENT_ID)

        print(id_info, flush=True)
        if not str(id_info['iss']).endswith('accounts.google.com'):
            raise ValueError('Wrong issuer.')

    except exceptions.GoogleAuthError as e1:
        logging.warning(f"Attempted login with invalid token: {token}; {e1}")
        abort(400)
    except ValueError as e2:
        logging.warning(f"Attempted login with invalid token: {token}; {e2}")
        abort(400)

    email = str(id_info['email'])
    if not email.endswith('@cam.ac.uk'):
        abort(400)

    if not bool(id_info['email_verified']):
        logging.warning(f"Unverified cam email: {email}")
        abort(400)

    # User ID stored in value 'sub'
    # See https://developers.google.com/identity/protocols/oauth2/openid-connect
    google_id = str(id_info['sub'])

    return google_id