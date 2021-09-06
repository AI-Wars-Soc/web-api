import os
import tarfile
import zipfile

from cuwais.config import config_file
from collections import namedtuple
from typing import Dict

SubmissionsData = namedtuple("SubmissionsData", ["base", "extensions"])

SUBMISSIONS_PATH = "/home/web_user/default_submissions/"

SUBMISSIONS: Dict[str, SubmissionsData] = {
    "chess": SubmissionsData("chess_base", ["chess_random_move"])
}

# Check that all submissions are present
for data in SUBMISSIONS.values():
    assert os.path.isdir(SUBMISSIONS_PATH + data.base)
    for ext in data.extensions:
        assert os.path.isdir(SUBMISSIONS_PATH + ext)

DEFAULT_SUBMISSION = config_file.get("gamemode.default_submission")
if DEFAULT_SUBMISSION is None:
    DEFAULT_SUBMISSION = SUBMISSIONS[config_file.get("gamemode.id")].extensions[0]

# Check that the config option is valid
assert DEFAULT_SUBMISSION in SUBMISSIONS[config_file.get("gamemode.id")].extensions

BASE_SUBMISSION_PATH = SUBMISSIONS_PATH + SUBMISSIONS[config_file.get("gamemode.id")].base
DEFAULT_SUBMISSION_PATH = SUBMISSIONS_PATH + DEFAULT_SUBMISSION


def make_zip(base_dir, addition_dir):
    zip_path = addition_dir + ".zip"
    with zipfile.ZipFile(zip_path, mode='w') as my_zipfile:
        def add_dir_to_zip(dir_to_zip):
            for root, dirs, files in os.walk(dir_to_zip):
                subdir = os.path.relpath(dir_to_zip, root)
                for name in files:
                    my_zipfile.write(os.path.join(root, name), arcname=os.path.join(subdir, name))

        add_dir_to_zip(base_dir)
        add_dir_to_zip(addition_dir)

    return zip_path


def make_tar(base_dir, addition_dir):
    tar_path = addition_dir + ".tar"
    with tarfile.open(name=tar_path, mode='w') as tar:
        tar.add(base_dir, arcname="")
        tar.add(addition_dir, arcname="")

    return tar_path


DEFAULT_SUBMISSION_ZIP_PATH = make_zip(BASE_SUBMISSION_PATH, DEFAULT_SUBMISSION_PATH)
DEFAULT_SUBMISSION_TAR_PATH = make_tar(BASE_SUBMISSION_PATH, DEFAULT_SUBMISSION_PATH)
