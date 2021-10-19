import hashlib
import io
import json
import logging
import tarfile
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any, Union

import cuwais
from cuwais.common import Outcome
from cuwais.config import config_file
from cuwais.database import User, Submission, Result, Match
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app import repo, nickname
from app.caching import cached
from app.repo import get_repo_path, AlreadyExistsException, RepoTooBigException


def get_user(user_id: Union[str, int]) -> Optional[User]:
    if user_id is None:
        return None

    user_id = int(user_id)

    with cuwais.database.create_session() as db_session:
        return db_session.query(User).get(user_id)


def generate_nickname(db_session: Session):
    tried = {}
    for i in range(1000):
        nick = nickname.get_new_name()
        if nick in tried:
            continue
        if db_session.query(User).filter(User.nickname == nick).first() is None:
            return nick
        tried += nick
    return "[FAILED TO GENERATE NICKNAME]"


def set_user_name_visible(db_session: Session, user: User, visible: bool) -> None:
    db_session.query(User).get(user.id).display_real_name = visible


def make_scoreboard_entry(user: User, score: Optional[int], init: int, outcomes: dict):
    return {"user_id": user.id,
            "score": 0 if score is None else (init + score),
            "score_text": ("" if score is None else "%.0f" % (init + score)),
            "is_bot": user.is_bot,
            "outcomes": outcomes}


@cached(ttl=300)
def get_scoreboard_data():
    with cuwais.database.create_session() as db_session:
        user_scores = db_session.query(
            User,
            func.sum(Result.points_delta).label("total_score")
        ).outerjoin(User.submissions) \
            .outerjoin(Submission.results) \
            .group_by(User.id) \
            .order_by("total_score") \
            .all()

        since = datetime.now() - timedelta(hours=24)
        counts = {}
        for outcome in Outcome:
            user_outcome_counts = db_session.query(
                User.id,
                func.count(Result.id)
            ).join(User.submissions) \
                .join(Submission.results) \
                .join(Result.match) \
                .filter(Result.outcome == int(outcome.value), Result.healthy == True, Result.points_delta != 0) \
                .filter(Match.match_date > since) \
                .group_by(User.id) \
                .all()

            counts[outcome] = user_outcome_counts

    # Convert outcomes to wins/losses/draws
    counts_by_outcome = {o: {user_id: count for user_id, count in counts[o]} for o in Outcome}

    init = int(config_file.get("initial_score"))
    outcomes = {user.id: {"wins": counts_by_outcome[Outcome.Win].get(user.id, 0),
                          "losses": counts_by_outcome[Outcome.Loss].get(user.id, 0),
                          "draws": counts_by_outcome[Outcome.Draw].get(user.id, 0)} for [user, _] in user_scores}
    scores = [make_scoreboard_entry(user, score, init, outcomes[user.id])
              for [user, score] in reversed(user_scores)]

    scores.sort(key=lambda e: e["score"], reverse=True)

    return scores


def get_scoreboard(db_session: Session, querying_user: User) -> List[Dict[str, Any]]:
    scores = get_scoreboard_data()

    new_scores = []
    found_you = False
    for vs in scores:
        user = db_session.query(User).get(vs["user_id"])

        if user is None:
            continue

        is_you = querying_user.id == vs["user_id"]
        if is_you:
            found_you = True

        new_scores.append({
            "user": user.to_public_dict(),
            "is_you": is_you,
            **vs
        })

    if not found_you:
        new_scores.append({
            "user": querying_user.to_public_dict(),
            "is_you": True,
            **make_scoreboard_entry(querying_user, None, 0, {"wins": 0, "losses": 0, "draws": 0})
        })

    return new_scores


@cached(ttl=300)
def get_leaderboard_graph_data():
    with cuwais.database.create_session() as db_session:
        delta_score_buckets = db_session.query(
            User,
            func.date_trunc('hour', Match.match_date),
            func.sum(Result.points_delta).label("delta_score")
        ).join(User.submissions) \
            .join(Submission.results) \
            .join(Result.match) \
            .group_by(func.date_trunc('hour', Match.match_date),
                      User.id) \
            .all()

    deltas = []
    for user, time, delta in delta_score_buckets:
        deltas.append({"user_id": user.id, "time": time.timestamp(), "delta": delta})

    return deltas


def get_leaderboard_graph(db_session: Session, querying_user_id: int):
    deltas = get_leaderboard_graph_data()

    users = {}
    init = int(config_file.get("initial_score"))
    for delta in deltas:
        other_user_id = delta['user_id']
        user = db_session.query(User).get(other_user_id)

        # If user has been deleted since the cache
        if user is None:
            del deltas[other_user_id]
            continue

        users[str(other_user_id)] = user.to_public_dict()
        users[str(other_user_id)]["is_you"] = other_user_id == querying_user_id

    return {"users": users, "deltas": deltas, "initial_score": init}


def get_all_user_submissions(db_session: Session, user: User, private=False) -> List[dict]:
    user_id = user.id
    subs = db_session.execute(
        select(Submission).where(Submission.user_id == user_id).order_by(Submission.submission_date)
    ).all()

    sub_dicts = [sub.to_private_dict() if private else sub.to_public_dict() for [sub] in reversed(subs)]
    sub_ids = {sub["submission_id"] for sub in sub_dicts}

    if private:
        untested = db_session.query(Submission.id) \
            .outerjoin(Submission.results) \
            .filter(Result.id == None, Submission.id.in_(sub_ids)) \
            .all()
        untested_ids = {u[0] for u in untested}

        healthy = db_session.query(
            Submission.id,
        ).join(Submission.results) \
            .group_by(Submission.id) \
            .filter(Result.healthy == True, Submission.id.in_(sub_ids)) \
            .all()
        healthy_ids = {u[0] for u in healthy}

        unhealthy_tested_ids = {s_id for s_id in sub_ids if s_id not in healthy_ids and s_id not in untested_ids}
        crash_matches = db_session.query(
            Submission.id,
            func.max(Match.id).label("match_id")
        ).join(Submission.results) \
            .join(Result.match) \
            .group_by(Submission.id) \
            .filter(Submission.id.in_(unhealthy_tested_ids)) \
            .subquery()

        crash_recordings = db_session.query(
            Submission.id,
            Match.recording,
            Result.result_code,
            Result.prints
        ).join(Submission.results) \
            .join(Result.match) \
            .join(
            crash_matches,
            and_(
                Submission.id == crash_matches.c.id,
                Match.id == crash_matches.c.match_id
            )
        ).all()

        crash_dict = {s_id: {"recording": json.loads(recording), "result": result, "prints": prints}
                      for s_id, recording, result, prints in crash_recordings}

        sub_dicts = [{**sub, "tested": sub["submission_id"] not in untested_ids,
                      "healthy": sub["submission_id"] in healthy_ids,
                      "crash": crash_dict.get(sub["submission_id"], None)}
                     for sub in sub_dicts]

    return sub_dicts


def create_git_submission(db_session: Session, user: User, url: str) -> int:
    files_hash = repo.download_repository(user.id, url)

    return create_submission(db_session, user, url, files_hash)


class SubmissionRawFileData(BaseModel):
    fileName: str
    data: str


def create_raw_files_submission(db_session: Session, user: User, files: List[SubmissionRawFileData]) -> int:
    url = "file://localfiles"

    size = sum([len(v) for f, v in files])
    if size > int(config_file.get("max_repo_size_bytes")):
        raise RepoTooBigException(url)

    # Calculate submission hash
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.data.encode())
    files_hash = cuwais.common.calculate_git_hash(user.id, digest.hexdigest(), url)

    logging.info(f"New raw submission with hash {files_hash}")
    archive_dir = get_repo_path(files_hash)
    if archive_dir.exists():
        raise AlreadyExistsException(url)

    # Create tar and save
    with tarfile.open(archive_dir, mode='w') as tar:
        for file in files:
            data = file.data.encode()
            fileobj = io.BytesIO(data)
            info = tarfile.TarInfo(name=file.fileName)
            info.size = len(data)
            tar.addfile(info, fileobj)

    return create_submission(db_session, user, url, files_hash)


def create_submission(db_session: Session, user: User, url: str, files_hash: str) -> int:
    now = datetime.now(tz=timezone.utc)
    submission = Submission(user_id=user.id, submission_date=now, url=url, active=True, files_hash=files_hash)
    db_session.add(submission)

    return submission.id


def is_submission_healthy(db_session: Session, submission_id: int):
    submission: Optional[Submission]
    submission = db_session.query(Submission).get(submission_id)

    if submission is None:
        return False

    res = db_session.query(
        Submission
    ).join(Submission.results) \
        .filter(Submission.id == submission.id, Result.healthy == True) \
        .first()

    if res is None:
        return False

    return True


def is_current_submission(db_session: Session, submission_id: int) -> bool:
    submission = db_session.query(Submission).get(submission_id)

    if submission is None:
        return False

    current_submission = get_current_submission(db_session, submission.user_id)

    if current_submission is None:
        return False

    return submission_id == current_submission.id


def get_current_submission(db_session: Session, user: Union[int, User]) -> Optional[Submission]:
    user_id = user.id if isinstance(user, User) else int(user)

    sub_date = db_session.query(
        func.max(Submission.submission_date).label('maxdate')
    ).join(Submission.results) \
        .group_by(Submission.user_id) \
        .filter(Submission.user_id == user_id, Submission.active == True, Result.healthy == True) \
        .first()

    if sub_date is None:
        return None

    sub_date = sub_date[0]

    submission = db_session.query(
        Submission
    ).filter(Submission.user_id == user_id) \
        .filter(Submission.submission_date == sub_date) \
        .first()

    return submission


def submission_is_owned_by_user(db_session: Session, submission_id: int, user_id: int) -> bool:
    if not isinstance(submission_id, int):
        return False
    if not isinstance(user_id, int):
        return False

    res = db_session.query(Submission).get(submission_id)

    if res is None:
        return False

    return res.user_id == user_id


def set_submission_enabled(db_session: Session, submission_id: int, enabled: bool):
    if not isinstance(submission_id, int):
        return
    if not isinstance(enabled, bool):
        return

    res = db_session.query(Submission).get(submission_id)

    if res is None:
        return

    res.active = enabled


@cached(ttl=300)
def get_submission_win_loss_data(submission_id: int):
    with cuwais.database.create_session() as db_session:
        vs = {}
        for outcome in Outcome:
            count = db_session.query(
                func.count(Result.id)
            ).join(Submission.results) \
                .group_by(Submission.id) \
                .filter(Submission.id == submission_id,
                        Result.outcome == outcome.value,
                        Result.points_delta != 0) \
                .first()

            count_healthy = db_session.query(
                func.count(Result.id)
            ).join(Submission.results) \
                .group_by(Submission.id) \
                .filter(Submission.id == submission_id,
                        Result.outcome == outcome.value,
                        Result.healthy == True,
                        Result.points_delta != 0) \
                .first()

            count = 0 if count is None else count[0]
            count_healthy = 0 if count_healthy is None else count_healthy[0]

            vs[outcome] = {"count": count, "count_healthy": count_healthy}

    return {"wins": vs[Outcome.Win]["count"],
            "losses": vs[Outcome.Loss]["count"],
            "draws": vs[Outcome.Draw]["count"],
            "wins_healthy": vs[Outcome.Win]["count_healthy"],
            "losses_healthy": vs[Outcome.Loss]["count_healthy"],
            "draws_healthy": vs[Outcome.Draw]["count_healthy"]}


def get_all_bot_submissions(db_session: Session) -> List[Tuple[User, Submission]]:
    return db_session.query(User, Submission).filter(User.is_bot == True).join(User.submissions).all()


def create_bot(db_session: Session, name: str) -> Optional[User]:
    if not isinstance(name, str):
        return None

    bot = User(nickname=name, real_name=name, is_bot=True)
    db_session.add(bot)

    return bot


def delete_bot(db_session: Session, bot_id: int) -> None:
    if not isinstance(bot_id, int):
        return

    db_session.query(Match) \
        .filter(Result.match_id == Match.id, Result.submission_id == Submission.id, Submission.user_id == bot_id) \
        .delete(synchronize_session='fetch')
    delete_user(db_session, bot_id)


def delete_user(db_session: Session, user_id: int) -> None:
    if not isinstance(user_id, int):
        return

    # Get submission hashes
    submissions = db_session.query(Submission) \
        .filter(Submission.user_id == user_id).all()
    submission_hashes = [s.files_hash for s in submissions]

    # Delete all data
    db_session.query(Result) \
        .filter(Result.submission_id == Submission.id, Submission.user_id == user_id) \
        .delete(synchronize_session='fetch')
    db_session.query(Submission) \
        .filter(Submission.user_id == user_id) \
        .delete(synchronize_session='fetch')
    db_session.delete(db_session.query(User).get(user_id))
    db_session.commit()

    # Delete archives
    for sub_hash in submission_hashes:
        repo.remove_submission_archive(sub_hash)


def delete_submission(db_session: Session, submission_id: int) -> None:
    if not isinstance(submission_id, int):
        return

    # Get submission hashes
    submission: Submission = db_session.query(Submission).get(submission_id)
    submission_hash = submission.files_hash

    # Delete all data
    db_session.query(Result) \
        .filter(Result.submission_id == submission_id) \
        .delete(synchronize_session='fetch')
    db_session.delete(db_session.query(Submission).get(submission_id))
    db_session.commit()

    # Delete archives
    repo.remove_submission_archive(submission_hash)


def is_submission_testing(db_session: Session, submission_id) -> bool:
    if not isinstance(submission_id, int):
        return False

    untested = db_session.query(Submission.id) \
        .outerjoin(Submission.results) \
        .filter(Result.id == None, Submission.id == submission_id) \
        .all()
    return len(untested) == 1


def get_submission_hash(db_session: Session, submission_id) -> Optional[str]:
    if not isinstance(submission_id, int):
        return None

    submission: Submission = db_session.query(Submission).get(submission_id)

    if submission is None:
        return None

    return submission.files_hash


def are_submissions_playable(db_session: Session, ids, userid):
    if not all(isinstance(x, int) for x in ids):
        return False
    if not isinstance(userid, int):
        return False

    for submission_id in ids:
        this_allowed = is_current_submission(db_session, submission_id) \
                       or submission_is_owned_by_user(db_session, submission_id, userid)

        this_allowed = this_allowed and is_submission_healthy(db_session, submission_id)

        if not this_allowed:
            return False

    return True
