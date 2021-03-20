import os
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Union, Any

import cuwais
from cuwais.database import User, Submission, Result, Match
from flask import session
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from server import repo


def save_user_id(user_id):
    session["cuwais_user_id"] = user_id


def get_user_id() -> Optional[int]:
    val = session.get("cuwais_user_id", "null")
    if val == "null":
        val = None
    else:
        val = int(val)
    return val


def get_user(database_session: Session) -> Optional[User]:
    user_id = get_user_id()
    return get_user_from_id(database_session, user_id)


def get_user_from_id(database_session: Session, user_id) -> Optional[User]:
    if user_id is None:
        return None

    return database_session.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()


def remove_user():
    session.pop("cuwais_user_id", None)


def make_or_get_google_user(google_id, name) -> int:
    with cuwais.database.create_session() as database_session:
        user = database_session.execute(
            select(User).where(User.google_id == google_id)
        ).scalar_one_or_none()

        if user is None:
            user = User(display_name=name, google_id=google_id)
            database_session.add(user)
            database_session.commit()

        return user.id


def get_scoreboard() -> List[Dict[str, Any]]:
    with cuwais.database.create_session() as database_session:
        user_scores = database_session.query(
            User,
            func.sum(Result.milli_points_delta).label("total_score")
        ).filter(Result.submission_id == Submission.id) \
            .filter(User.id == Submission.user_id) \
            .group_by(User.id) \
            .order_by("total_score") \
            .all()

    init = int(os.getenv("INITIAL_SCORE"))
    scores = [{"user": user.to_public_dict(),
               "score": init + (score / 1000)}
              for [user, score] in user_scores]

    return scores


def get_all_user_submissions(database_session: Session, user_id: int, private=False) -> List[dict]:
    subs = database_session.execute(
        select(Submission).where(Submission.user_id == user_id).order_by(Submission.submission_date)
    ).all()

    return [sub.to_private_dict() if private else sub.to_public_dict() for [sub] in reversed(subs)]


def create_submission(user_id: int, url: str) -> int:
    files_hash = repo.download_repository(user_id, url)

    with cuwais.database.create_session() as database_session:
        now = datetime.now(tz=timezone.utc)
        submission = Submission(user_id=user_id, submission_date=now, url=url, active=True, files_hash=files_hash)
        database_session.add(submission)
        database_session.commit()

        return submission.id
