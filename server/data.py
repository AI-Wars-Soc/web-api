import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any

import cuwais
from cuwais.common import Outcome
from cuwais.database import User, Submission, Result, Match
from flask import session
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session

from server import repo
from server.caching import cached


def save_user_id(user_id):
    session["cuwais_user_id"] = user_id


def get_user_id() -> Optional[int]:
    val = session.get("cuwais_user_id", "null")
    if val == "null":
        val = None
    else:
        val = int(val)
    return val


def get_user() -> Optional[User]:
    user_id = get_user_id()
    return get_user_from_id(user_id)


def get_user_from_id(user_id) -> Optional[User]:
    if user_id is None:
        return None

    with cuwais.database.create_session() as database_session:
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


@cached(ttl=300)
def get_scoreboard_data():
    with cuwais.database.create_session() as database_session:
        user_scores = database_session.query(
            User,
            func.sum(Result.points_delta).label("total_score")
        ).join(User.submissions) \
            .join(Submission.results) \
            .group_by(User.id) \
            .order_by(desc("total_score")) \
            .all()

        since = datetime.now() - timedelta(hours=24)
        counts = {}
        for outcome in Outcome:
            user_outcome_counts = database_session.query(
                User.id,
                func.count(Result.id)
            ).join(User.submissions)\
                .join(Submission.results)\
                .join(Result.match)\
                .filter(Result.outcome == int(outcome.value), Result.healthy == True)\
                .filter(Match.match_date > since)\
                .group_by(User.id)\
                .all()

            counts[outcome] = user_outcome_counts

    # Convert outcomes to wins/losses/draws
    counts_by_outcome = {o: {user_id: count for user_id, count in counts[o]} for o in Outcome}

    init = int(os.getenv("INITIAL_SCORE"))
    scores = [{"user": user.to_public_dict(),
               "score": init + score,
               "outcomes": {"wins": counts_by_outcome[Outcome.Win].get(user.id, 0),
                            "losses": counts_by_outcome[Outcome.Loss].get(user.id, 0),
                            "draws": counts_by_outcome[Outcome.Draw].get(user.id, 0)}}
              for [user, score] in user_scores]

    return scores


def get_scoreboard(user_id) -> List[Dict[str, Any]]:
    scores = get_scoreboard_data()

    scores = [{
        "is_you": user_id == vs["user"]["user_id"],
        **vs
    } for vs in scores]

    return scores


@cached(ttl=300)
def get_leaderboard_graph_data():
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
        users[user.id]["is_you"] = False
        users[user.id]["is_bot"] = user.is_bot

    return {"users": users, "deltas": deltas, "initial_score": init}


def get_leaderboard_graph(user_id):
    values = get_leaderboard_graph_data()

    if user_id in values["users"]:
        values["users"][user_id]["is_you"] = True

    return values


def get_all_user_submissions(user_id: int, private=False) -> List[dict]:
    with cuwais.database.create_session() as database_session:
        subs = database_session.execute(
            select(Submission).where(Submission.user_id == user_id).order_by(Submission.submission_date)
        ).all()

        sub_dicts = [sub.to_private_dict() if private else sub.to_public_dict() for [sub] in reversed(subs)]
        sub_ids = {sub["submission_id"] for sub in sub_dicts}

        if private:
            untested = database_session.query(Submission.id) \
                .outerjoin(Submission.results) \
                .filter(Result.id == None, Submission.id.in_(sub_ids)) \
                .all()
            untested_ids = {u[0] for u in untested}

            healthy = database_session.query(
                Submission.id,
            ).join(Submission.results) \
                .group_by(Submission.id) \
                .filter(Result.healthy == True, Submission.id.in_(sub_ids)) \
                .all()
            healthy_ids = {u[0] for u in healthy}

            unhealthy_tested_ids = {s_id for s_id in sub_ids if s_id not in healthy_ids and s_id not in untested_ids}
            crash_matches = database_session.query(
                Submission.id,
                func.max(Match.id).label("match_id")
            ).join(Submission.results)\
                .join(Result.match)\
                .group_by(Submission.id)\
                .filter(Submission.id.in_(unhealthy_tested_ids))\
                .subquery()

            crash_recordings = database_session.query(
                Submission.id,
                Match.recording
            ).join(Submission.results)\
                .join(Result.match)\
                .join(
                crash_matches,
                and_(
                    Submission.id == crash_matches.c.id,
                    Match.id == crash_matches.c.match_id
                )
            ).all()

            crash_recording_dict = {s_id: json.loads(recording) for s_id, recording in crash_recordings}

            sub_dicts = [{**sub, "tested": sub["submission_id"] not in untested_ids,
                          "healthy": sub["submission_id"] in healthy_ids,
                          "crash_recording": crash_recording_dict.get(sub["submission_id"], {})}
                         for sub in sub_dicts]

    return sub_dicts


def create_submission(user_id: int, url: str) -> int:
    files_hash = repo.download_repository(user_id, url)

    with cuwais.database.create_session() as database_session:
        now = datetime.now(tz=timezone.utc)
        submission = Submission(user_id=user_id, submission_date=now, url=url, active=True, files_hash=files_hash)
        database_session.add(submission)
        database_session.commit()

        return submission.id


def get_current_submission(user_id) -> Optional[Submission]:
    with cuwais.database.create_session() as database_session:
        sub_date = database_session.query(
            func.max(Submission.submission_date).label('maxdate')
        ).join(Submission.results)\
            .group_by(Submission.user_id) \
            .filter(Submission.user_id == user_id, Submission.active == True, Result.healthy == True) \
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


def submission_is_owned_by_user(submission_id: int, user_id: int):
    with cuwais.database.create_session() as database_session:
        res = database_session.query(Submission).get(submission_id)

    if res is None:
        return False

    return res.user_id == user_id


def set_submission_enabled(submission_id: int, enabled: bool):
    with cuwais.database.create_session() as database_session:
        res = database_session.query(Submission).get(submission_id)

        if res is None:
            return

        res.active = enabled

        database_session.commit()


def get_submission_summary_data(submission_id: int):
    with cuwais.database.create_session() as database_session:
        vs = {}
        for outcome in Outcome:
            c = database_session.query(
                func.count(Result.id)
            ).join(Submission.results)\
                .group_by(Submission.id)\
                .filter(Submission.id == submission_id, Result.outcome == outcome.value)\
                .first()

            ch = database_session.query(
                func.count(Result.id)
            ).join(Submission.results)\
                .group_by(Submission.id)\
                .filter(Submission.id == submission_id,
                        Result.outcome == outcome.value,
                        Result.healthy == True)\
                .first()

            c = 0 if c is None else c[0]
            ch = 0 if ch is None else ch[0]

            vs[outcome] = {"count": c, "count_healthy": ch}

    return {"wins": vs[Outcome.Win]["count"], "losses": vs[Outcome.Loss]["count"], "draws": vs[Outcome.Draw]["count"],
            "wins_healthy": vs[Outcome.Win]["count_healthy"], "losses_healthy": vs[Outcome.Loss]["count_healthy"],
            "draws_healthy": vs[Outcome.Draw]["count_healthy"]}


def get_all_bot_submissions() -> List[Tuple[User, Submission]]:
    with cuwais.database.create_session() as database_session:
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
