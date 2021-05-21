import logging
import os

from cuwais.config import config_file
from cuwais.database import User
from google.auth import exceptions
from google.oauth2 import id_token
import google.auth.transport.requests
import cachecontrol
import requests

from werkzeug.exceptions import abort

from server import data

session = requests.session()
cached_session = cachecontrol.CacheControl(session)
_client_id = config_file.get("google_client_id")


def get_user_from_google_token(db_session, token) -> User:
    id_info = None
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        google_request = google.auth.transport.requests.Request(session=cached_session)
        id_info = id_token.verify_oauth2_token(token, google_request, _client_id)

        if not str(id_info['iss']).endswith('accounts.google.com'):
            raise ValueError('Wrong issuer.')

    except exceptions.GoogleAuthError as e1:
        logging.warning(f"Attempted login with invalid token: {token}; {id_info}; {e1}")
        abort(400)
    except ValueError as e2:
        logging.warning(f"Attempted login with invalid token: {token}; {id_info}; {e2}")
        abort(400)

    email = str(id_info['email'])
    required_domain = config_file.get("config.allowed_email_domain")
    if required_domain is not None and not email.endswith(f'@{required_domain}'):
        logging.warning(f"Non-uni email: {email}; {id_info}")
        abort(400)

    if not bool(id_info['email_verified']):
        logging.warning(f"Unverified email: {email}; {id_info}")
        abort(400)

    # User ID stored in value 'sub'
    # See https://developers.google.com/identity/protocols/oauth2/openid-connect
    google_id = str(id_info['sub'])
    name = str(id_info['name'])

    user = data.make_or_get_google_user(db_session, google_id, name)

    return user
