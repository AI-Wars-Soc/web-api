from cuwais.config import config_file

with open("/run/secrets/secret_key") as secrets_file:
    secret = "".join(secrets_file.readlines())
    SECRET_KEY = secret
DEBUG = config_file.get("debug")
SECURE = config_file.get("secure")

PROFILE = config_file.get("profile")

SERVER_NAME = config_file.get("front_end.server_name")

ACCESS_TOKEN_EXPIRE_MINUTES = config_file.get("front_end.access_token_expire_minutes")
ACCESS_TOKEN_ALGORITHM = config_file.get("front_end.access_token_algorithm")
