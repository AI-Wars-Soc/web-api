import os
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
