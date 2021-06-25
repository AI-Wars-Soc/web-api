import logging
import os
import re
from io import StringIO
from pathlib import Path
from shutil import rmtree
from threading import Lock

import cuwais.common
import sh as sh
from cuwais.config import config_file

_cloning_dirs_mutex = Lock()


GIT_BASE_DIR = '/home/web_user/repositories/'
GIT_HASH_RE = re.compile(r"^(?P<hash>[0-9a-f]{40})\s*HEAD$", re.MULTILINE)


class InvalidGitURL(RuntimeError):
    def __init__(self, msg, url):
        RuntimeError.__init__(self, msg)
        self.msg = msg
        self.url = url


class AlreadyExistsException(RuntimeError):
    pass


class AlreadyCloningException(RuntimeError):
    pass


class RepoTooBigException(RuntimeError):
    pass


class CantCloneException(RuntimeError):
    pass


def download_repository(user_id: int, url: str) -> str:
    if "\n" in url:
        raise InvalidGitURL("Invalid URL", url)

    buf = StringIO()
    try:
        sh.git("ls-remote", url, _out=buf)
    except sh.ErrorReturnCode:
        raise InvalidGitURL("Invalid GIT URL", url)

    ping_string = str(buf.getvalue())
    match = GIT_HASH_RE.match(ping_string)
    if match is None:
        raise InvalidGitURL("GIT URL has no HEAD", url)

    commit_hash = match.group(1)
    files_hash = cuwais.common.calculate_git_hash(user_id, commit_hash, url)

    clone_dir = Path(GIT_BASE_DIR, files_hash)
    clone_dir_str = str(clone_dir.absolute())
    archive_dir = Path(GIT_BASE_DIR, files_hash + ".tar")
    archive_dir_str = str(archive_dir.absolute())

    _cloning_dirs_mutex.acquire()
    try:
        if clone_dir.exists():
            raise AlreadyCloningException(url)

        if archive_dir.exists():
            raise AlreadyExistsException(url)

        os.mkdir(clone_dir)
    finally:
        _cloning_dirs_mutex.release()

    try:
        sh.git.clone(url, clone_dir_str, "--depth=1")

        size = get_dir_size_bytes(clone_dir_str)
        if size > int(config_file.get("max_repo_size_bytes")):
            # TODO: Cache too big entries in redis
            raise RepoTooBigException(url)

        sh.git.archive("--output=" + archive_dir_str, "--format=tar", "HEAD", _cwd=clone_dir_str)
    except Exception as e:
        logging.exception(e)
        raise CantCloneException(url)
    finally:
        if clone_dir.exists():
            rmtree(clone_dir_str)

    return files_hash


def remove_submission_archive(files_hash):
    archive_dir = Path(GIT_BASE_DIR, files_hash + ".tar")
    os.remove(archive_dir)


def get_dir_size_bytes(path) -> int:
    total_size = 0
    for dir_path, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dir_path, f)
            total_size += os.path.getsize(fp)

    return total_size
