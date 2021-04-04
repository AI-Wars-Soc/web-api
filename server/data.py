import os
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Union, Any

import cuwais
from cuwais.common import Outcome
from cuwais.database import User, Submission, Result, Match
from flask import session
from sqlalchemy import select, func, and_, desc
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

    return database_session.query(User).get(user_id)


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


def get_scoreboard(user_id) -> List[Dict[str, Any]]:
    # TODO: cache these queries and only re-run them every 5 mins or so
    with cuwais.database.create_session() as database_session:
        user_scores = database_session.query(
            User,
            func.sum(Result.points_delta).label("total_score")
        ).filter(Result.submission_id == Submission.id) \
            .filter(User.id == Submission.user_id) \
            .group_by(User.id) \
            .order_by(desc("total_score")) \
            .all()

        counts = {}
        for outcome in Outcome:
            user_outcome_counts = database_session.query(
                User.id,
                func.count(Result.id)
            ).join(User.submissions)\
                .join(Submission.results)\
                .filter(Result.outcome == int(outcome.value))\
                .group_by(User.id)\
                .all()

            counts[outcome] = user_outcome_counts

    # Convert outcomes to wins/losses/draws
    counts_by_outcome = {o: {user_id: count for user_id, count in counts[o]} for o in Outcome}

    init = int(os.getenv("INITIAL_SCORE"))
    scores = [{"user": user.to_public_dict(),
               "score": init + score,
               "is_you": user_id == user.id,
               "outcomes": {"wins": counts_by_outcome[Outcome.Win][user.id],
                            "losses": counts_by_outcome[Outcome.Loss][user.id],
                            "draws": counts_by_outcome[Outcome.Draw][user.id]}}
              for [user, score] in user_scores]

    return scores


def get_leaderboard_graph(user_id):
    with cuwais.database.create_session() as database_session:
        delta_score_buckets = database_session.query(
            User,
            func.date_trunc('hour', Match.match_date),
            func.sum(Result.points_delta).label("delta_score")
        ).filter(Result.submission_id == Submission.id,
                 User.id == Submission.user_id) \
            .join(Result.match) \
            .group_by(func.date_trunc('hour', Match.match_date),
                      User.id)\
            .all()

    users = {}
    deltas = []
    init = int(os.getenv("INITIAL_SCORE"))
    for user, time, delta in delta_score_buckets:
        deltas.append({"user_id": user.id, "time": time.timestamp(), "delta": delta})
        users[user.id] = user.to_public_dict()
        users[user.id]["is_you"] = (user_id == user.id)
        users[user.id]["is_bot"] = user.is_bot

    return {"users": users, "deltas": deltas, "initial_score": init}


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


def get_current_submission(database_session, user_id) -> Optional[Submission]:
    sub_date = database_session.query(
        func.max(Submission.submission_date).label('maxdate')
    ).group_by(Submission.user_id) \
        .filter(Submission.user_id == user_id) \
        .filter(Submission.active == True) \
        .first()

    if sub_date is None:
        return None

    sub_date = sub_date[0]

    submission = database_session.query(
        Submission
    ).filter(Submission.user_id == user_id) \
        .filter(Submission.submission_date == sub_date) \
        .first()

    return submission


def submission_is_owned_by_user(database_session, submission_id: int, user_id: int):
    res = database_session.query(Submission).get(submission_id)

    if res is None:
        return False

    return res.user_id == user_id


def set_submission_enabled(database_session, submission_id: int, enabled: bool):
    res = database_session.query(Submission).get(submission_id)

    if res is None:
        return

    res.active = enabled

    database_session.commit()


def get_all_bot_submissions(database_session) -> List[Tuple[User, Submission]]:
    return database_session.query(User, Submission).filter(User.is_bot == True).join(User.submissions).all()


def create_bot(name):
    with cuwais.database.create_session() as database_session:
        bot = User(display_name=name, is_bot=True)
        database_session.add(bot)
        database_session.commit()

        return bot.id


def delete_bot(bot_id):
    with cuwais.database.create_session() as database_session:
        database_session.query(Match).join(Match.results).join(Result.submission)\
                                                               .filter(Submission.user_id == bot_id).delete()
        database_session.query(Result).join(Result.submission).filter(Submission.user_id == bot_id).delete()
        database_session.query(Submission).filter(Submission.user_id == bot_id).delete()
        bot = database_session.query(User).get(bot_id)
        database_session.delete(bot)
        database_session.commit()
