import os
from datetime import datetime, timezone
from typing import Optional, List, Tuple

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


def get_scoreboard() -> List[Tuple[dict, int]]:
    with cuwais.database.create_session() as database_session:
        subq = database_session.query(
            Submission.user_id,
            func.max(Submission.submission_date).label('maxdate')
        ).group_by(Submission.user_id) \
            .filter(Submission.active == True) \
            .subquery('t2')

        most_recent_submissions = database_session.query(Submission).join(
            subq,
            and_(
                Submission.user_id == subq.c.user_id,
                Submission.submission_date == subq.c.maxdate
            )
        ).subquery('t3')

        user_scores = database_session.query(
            Submission.user_id,
            func.sum(Result.milli_points_delta)
        ).filter(Result.submission_id == Submission.id) \
            .group_by(Submission.user_id) \
            .join(
            most_recent_submissions,
            and_(
                Submission.user_id == most_recent_submissions.c.user_id
            )
        ).all()

        init = int(os.getenv("INITIAL_SCORE")) * 1000

        results = [(a, b + init) for [a, b] in user_scores]

    return sorted(results, key=lambda t: t[1], reverse=True)


def get_all_user_submissions(database_session: Session, user_id: int, private=False) -> List[dict]:
    subs = database_session.execute(
        select(Submission).where(Submission.user_id == user_id).order_by(Submission.submission_date)
    ).all()

    return [sub.to_private_dict() if private else sub.to_public_dict() for sub in subs]


def create_submission(user_id: int, url: str) -> int:
    files_hash = repo.download_repository(user_id, url)

    with cuwais.database.create_session() as database_session:
        now = datetime.now(tz=timezone.utc)
        submission = Submission(user_id=user_id, submission_date=now, url=url, active=True, files_hash=files_hash)
        database_session.add(submission)

        return submission.id
