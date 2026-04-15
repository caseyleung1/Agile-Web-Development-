from __future__ import annotations

from datetime import date, datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False, default="")
    title = db.Column(db.String(120), nullable=True)
    language = db.Column(db.String(32), nullable=False, default="English")
    notify_study_reminder = db.Column(db.Boolean, default=True)
    notify_daily_goal = db.Column(db.Boolean, default=True)
    notify_friend = db.Column(db.Boolean, default=False)
    notify_new_sets = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    study_sets = db.relationship("StudySet", backref="owner", lazy="dynamic", cascade="all, delete-orphan")
    progress = db.relationship("StudyProgress", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class StudySet(db.Model):
    __tablename__ = "study_sets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    cards = db.relationship(
        "Card",
        backref="study_set",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Card.id",
    )


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    study_set_id = db.Column(db.Integer, db.ForeignKey("study_sets.id"), nullable=False, index=True)
    term = db.Column(db.Text, nullable=False)
    definition = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False, default="")
    option_b = db.Column(db.String(500), nullable=False, default="")
    option_c = db.Column(db.String(500), nullable=False, default="")
    option_d = db.Column(db.String(500), nullable=False, default="")
    correct_index = db.Column(db.Integer, nullable=False, default=0)  # 0-3

    progress_entries = db.relationship("StudyProgress", backref="card", lazy="dynamic", cascade="all, delete-orphan")

    def options_list(self) -> list[str]:
        return [self.option_a, self.option_b, self.option_c, self.option_d]


class StudyProgress(db.Model):
    __tablename__ = "study_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), nullable=False, index=True)
    rating = db.Column(db.String(16), nullable=True)  # easy, medium, hard
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "card_id", name="uq_user_card_progress"),)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    study_set_id = db.Column(db.Integer, db.ForeignKey("study_sets.id"), nullable=False, index=True)
    mode = db.Column(db.String(32), nullable=False)  # quiz, timed
    score_percent = db.Column(db.Float, nullable=True)
    correct_count = db.Column(db.Integer, default=0)
    incorrect_count = db.Column(db.Integer, default=0)
    missed_count = db.Column(db.Integer, default=0)
    detail_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class StudyDayStat(db.Model):
    """Aggregated cards studied per user per local day (for analytics chart)."""

    __tablename__ = "study_day_stats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    day = db.Column(db.Date, nullable=False)
    cards_studied = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("user_id", "day", name="uq_user_day_stat"),)


def difficulty_counts_for_set(user_id: int, study_set_id: int) -> dict[str, int]:
    from sqlalchemy import func

    q = (
        db.session.query(StudyProgress.rating, func.count(StudyProgress.id))
        .filter(StudyProgress.user_id == user_id)
        .join(Card, StudyProgress.card_id == Card.id)
        .filter(Card.study_set_id == study_set_id)
        .group_by(StudyProgress.rating)
    )
    rows = {r: 0 for r in ("easy", "medium", "hard")}
    for rating, cnt in q.all():
        if rating in rows:
            rows[rating] = cnt
    return rows


def bump_cards_studied(user_id: int, day: date | None = None) -> None:
    if day is None:
        day = date.today()
    stat = StudyDayStat.query.filter_by(user_id=user_id, day=day).first()
    if stat:
        stat.cards_studied += 1
    else:
        db.session.add(StudyDayStat(user_id=user_id, day=day, cards_studied=1))
