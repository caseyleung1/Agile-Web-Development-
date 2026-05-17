from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    streak = db.Column(db.Integer, default=0)
    achievements = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, nullable=True)
    avatar_emoji = db.Column(db.String(8), nullable=True)
    study_sets = db.relationship("StudySet", back_populates="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_streak(self):
            today = datetime.now(timezone.utc).date()
            if self.last_active:
                diff = today - self.last_active.date()
                if diff.days == 1:
                    self.streak += 1       # consecutive day
                elif diff.days > 1:
                    self.streak = 1        # missed a day, reset
            else:
                self.streak = 1            # first login ever
            self.last_active = datetime.now(timezone.utc)

    def update_achievements(self):
        count = 0
        # 1 achievement for first study set
        if len(self.study_sets) >= 1:
            count += 1
        # 1 achievement for 5 study sets
        if len(self.study_sets) >= 5:
            count += 1
        # 1 achievement for 7 day streak
        if self.streak >= 7:
            count += 1
        # 1 achievement for 10 study sets
        if len(self.study_sets) >= 10:
            count += 1
        self.achievements = count

study_set_tag = db.Table(
    "study_set_tag",
    db.Column("study_set_id", db.Integer, db.ForeignKey("study_set.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False, index=True)

    study_sets = db.relationship(
        "StudySet", secondary=study_set_tag, back_populates="tags"
    )

    @staticmethod
    def normalize(raw):
        """Lower-case, hyphenate spaces, strip everything that isn't a-z0-9 or hyphen."""
        if not raw:
            return ""
        s = raw.strip().lower().replace(" ", "-")
        out = []
        for ch in s:
            if ch.isalnum() or ch == "-":
                out.append(ch)
        return "".join(out).strip("-")[:40]

    @classmethod
    def get_or_create(cls, raw):
        name = cls.normalize(raw)
        if not name:
            return None
        existing = cls.query.filter_by(name=name).first()
        if existing:
            return existing
        tag = cls(name=name)
        db.session.add(tag)
        return tag


class StudySet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    cover_emoji = db.Column(db.String(8), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", back_populates="study_sets")
    flashcards = db.relationship(
        "Flashcard",
        back_populates="study_set",
        lazy=True,
        cascade="all, delete-orphan",
    )
    tags = db.relationship(
        "Tag", secondary=study_set_tag, back_populates="study_sets", lazy="joined"
    )


class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    study_set_id = db.Column(db.Integer, db.ForeignKey("study_set.id"), nullable=False)
    study_set = db.relationship("StudySet", back_populates="flashcards")


class Favorite(db.Model):
    """A user's bookmark of a study set (their own or someone else's)."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    study_set_id = db.Column(
        db.Integer, db.ForeignKey("study_set.id"), nullable=False, index=True
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "study_set_id", name="uq_favorite_user_set"),
    )

    user = db.relationship(
        "User",
        backref=db.backref("favorites", lazy=True, cascade="all, delete-orphan"),
    )
    study_set = db.relationship(
        "StudySet",
        backref=db.backref("favorited_by", lazy=True, cascade="all, delete-orphan"),
    )


class StudySession(db.Model):
    """A completed Quiz or Time-Game run by a user against one of their sets."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    study_set_id = db.Column(
        db.Integer, db.ForeignKey("study_set.id"), nullable=False, index=True
    )
    mode = db.Column(db.String(20), nullable=False)  # "quiz" or "time"
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)   # 0.0 – 1.0
    finished_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user = db.relationship(
        "User",
        backref=db.backref("study_sessions", lazy=True, cascade="all, delete-orphan"),
    )
    study_set = db.relationship(
        "StudySet",
        backref=db.backref("sessions", lazy=True, cascade="all, delete-orphan"),
    )
