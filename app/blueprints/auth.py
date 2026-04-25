from flask import Blueprint, redirect, render_template, request, session, url_for
from app.decorators import current_user_id
from app.extensions import db
from app.models import StudyDayStat, StudyProgress, StudySet, User

auth_bp = Blueprint("auth", __name__, url_prefix="")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user_id():
        return redirect(url_for("main.dashboard"))
    error = None
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        agree = request.form.get("terms") == "on"
        if not all([full_name, email, password]):
            error = "Please fill in all required fields."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif not agree:
            error = "Please accept the terms to continue."
        elif User.query.filter_by(email=email).first():
            error = "An account with this email already exists."
        else:
            u = User(email=email, full_name=full_name)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            session["user_id"] = u.id
            return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html", error=error, full_name=full_name, email=email, agree=agree)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user_id():
        return redirect(url_for("main.dashboard"))
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        u = User.query.filter_by(email=email).first()
        if not u or not u.check_password(password):
            error = "Invalid email or password."
        else:
            session["user_id"] = u.id
            nxt = request.args.get("next") or request.form.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))


def user_stats(user_id: int) -> dict:
    u = User.query.get(user_id)
    if not u:
        return {}
    set_count = StudySet.query.filter_by(user_id=user_id).count()
    studied = StudyProgress.query.filter_by(user_id=user_id).count()
    streak = _compute_streak(user_id)
    return {
        "full_name": u.full_name,
        "title": u.title or "Student",
        "sets": set_count,
        "cards_studied": studied,
        "streak_days": streak,
        "achievements": min(12, set_count + (streak // 3)),
    }


def _compute_streak(user_id: int) -> int:
    days = (
        db.session.query(StudyDayStat.day)
        .filter(StudyDayStat.user_id == user_id, StudyDayStat.cards_studied > 0)
        .order_by(StudyDayStat.day.desc())
        .all()
    )
    if not days:
        return 0
    from datetime import date, timedelta

    today = date.today()
    streak = 0
    d = today
    day_set = {row[0] for row in days}
    while d in day_set:
        streak += 1
        d -= timedelta(days=1)
    return streak
