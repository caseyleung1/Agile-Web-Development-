from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from app import db
from app.models import Favorite, Flashcard, StudySession, StudySet, Tag, User


main = Blueprint("main", __name__)


def get_owned_study_set_or_404(study_set_id):
    study_set = StudySet.query.filter_by(
        id=study_set_id,
        user_id=current_user.id,
    ).first()
    if study_set is None:
        abort(404)
    return study_set


def get_playable_study_set_or_404(study_set_id):
    """Return the set if the current user can play it (owns it or it's public)."""
    study_set = StudySet.query.get_or_404(study_set_id)
    if study_set.user_id != current_user.id and not study_set.is_public:
        abort(404)
    return study_set


def back_url_for_set(study_set):
    """Where the play screens' '← back' link should go for this user/set."""
    if study_set.user_id == current_user.id:
        return url_for("main.study_set_detail", study_set_id=study_set.id)
    return url_for("main.browse_public_study_set", study_set_id=study_set.id)


@main.route("/")
def index():
    recent_public_sets = (
        StudySet.query.filter_by(is_public=True)
        .order_by(StudySet.id.desc())
        .limit(5)
        .all()
    )
    return render_template("index.html", recent_public_sets=recent_public_sets)


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        terms = request.form.get("terms")

        if not terms:
            flash("You must agree to the Terms and Conditions.", "danger")
            return render_template("register.html"), 400

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html"), 400

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("An account with that name or email already exists.", "danger")
            return render_template("register.html"), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created! Welcome!", "success")
        return redirect(url_for("main.index"))

    return render_template("register.html")

@main.route('/terms')
def terms():
    return render_template('terms.html')

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        login_identifier = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.email == login_identifier) | (User.username == login_identifier)
        ).first()

        if user is None or not user.check_password(password):
            flash("Invalid email/username or password.", "danger")
            return render_template("login.html", email=login_identifier), 400

        user.update_streak()
        user.update_achievements()
        db.session.commit()

        login_user(user)

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)

        return redirect(url_for("main.index"))

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.")
    return redirect(url_for("main.index"))


@main.route("/setting", methods=["GET", "POST"])
@main.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("setting.html"), 400

        existing_user = User.query.filter(
            ((User.username == username) | (User.email == email))
            & (User.id != current_user.id)
        ).first()

        if existing_user:
            flash("That username or email is already in use.", "danger")
            return render_template("setting.html"), 400

        current_user.username = username
        current_user.email = email

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("main.settings"))

    return render_template("setting.html")

DELIMITER_MAP = {
    "tab":   "\t",
    "comma": ",",
    "dash":  "-",
    "pipe":  "|",
}


def _parse_bulk(text, delimiter_key):
    """Parse pasted/CSV text into a list of (term, definition) tuples."""
    delim = DELIMITER_MAP.get(delimiter_key, "\t")
    pairs = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if delim not in line:
            continue
        term, _, definition = line.partition(delim)
        # If the chosen delim was a comma, allow second-comma-and-beyond as part of the definition.
        # partition() already handles that — only splits on the first occurrence.
        term = term.strip().strip('"').strip()
        definition = definition.strip().strip('"').strip()
        if term and definition:
            pairs.append((term, definition))
    return pairs


def _guess_delimiter(text):
    """Pick tab/comma/pipe/dash by whichever yields the most card pairs."""
    best_key = "tab"
    best_count = 0
    for key in DELIMITER_MAP:
        count = len(_parse_bulk(text, key))
        if count > best_count:
            best_count = count
            best_key = key
    return best_key


@main.route("/settings/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("Please fill in all password fields.", "danger")
        return redirect(url_for("main.settings"))

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("main.settings"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("main.settings"))

    if len(new_password) < 6:
        flash("Password must be at least 6 characters long.", "danger")
        return redirect(url_for("main.settings"))

    if current_user.check_password(new_password):
        flash("New password must be different from your current password.", "danger")
        return redirect(url_for("main.settings"))

    current_user.set_password(new_password)
    db.session.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for("main.settings"))

@main.route("/study-sets/new", methods=["GET", "POST"])
@login_required
def create_study_set():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        mode = request.form.get("input_mode", "form")  # form | paste | upload

        pairs = []
        if mode == "paste":
            text = request.form.get("bulk_text", "")
            delim = request.form.get("bulk_delimiter") or _guess_delimiter(text)
            pairs = _parse_bulk(text, delim)
        elif mode == "upload":
            uploaded = request.files.get("bulk_file")
            if uploaded and uploaded.filename:
                try:
                    text = uploaded.read().decode("utf-8", errors="replace")
                except Exception:
                    text = ""
                # Default to comma for .csv, tab for .tsv, else fall back to form field.
                name = uploaded.filename.lower()
                guess = "comma" if name.endswith(".csv") else "tab" if name.endswith(".tsv") else None
                pairs = _parse_bulk(text, guess or _guess_delimiter(text))
        else:
            terms = request.form.getlist("term")
            definitions = request.form.getlist("definition")
            pairs = [
                (t.strip(), d.strip())
                for t, d in zip(terms, definitions)
                if t.strip() and d.strip()
            ]

        flashcards = [Flashcard(question=t, answer=d) for t, d in pairs]

        if not title or not flashcards:
            flash("Add a title and at least one complete flashcard.")
            return render_template("create_studyset.html"), 400

        # Cover emoji (we trust the picker; trim to 8 chars max).
        cover_emoji = (request.form.get("cover_emoji") or "").strip()[:8] or None

        # Tags: comma- (or space-) separated, normalized + de-duped.
        tag_objects = []
        raw_tags = request.form.get("tags", "")
        seen = set()
        for token in raw_tags.replace(",", " ").split():
            tag = Tag.get_or_create(token)
            if tag is None or tag.name in seen:
                continue
            seen.add(tag.name)
            tag_objects.append(tag)

        study_set = StudySet(
            title=title,
            description=description,
            cover_emoji=cover_emoji,
            owner=current_user,
            flashcards=flashcards,
            tags=tag_objects,
        )
        db.session.add(study_set)
        db.session.commit()

        flash(f"Study set created with {len(flashcards)} card{'s' if len(flashcards) != 1 else ''}.")
        return redirect(url_for("main.study_set_detail", study_set_id=study_set.id))

    return render_template("create_studyset.html")


@main.route("/study-sets")
@login_required
def study_sets():
    user_study_sets = (
        StudySet.query.filter_by(user_id=current_user.id)
        .order_by(StudySet.id.desc())
        .all()
    )
    total_cards = sum(len(s.flashcards) for s in user_study_sets)
    public_count = sum(1 for s in user_study_sets if s.is_public)
    return render_template(
        "my_study_sets.html",
        study_sets=user_study_sets,
        total_cards=total_cards,
        total_sets=len(user_study_sets),
        public_count=public_count,
    )


# Achievement catalogue — keep in sync with User.update_achievements()
ACHIEVEMENTS = [
    ("first-set",     "First steps",     "Created your first study set",     "fa-shoe-prints"),
    ("five-sets",     "Collector",       "Built 5 study sets",               "fa-layer-group"),
    ("week-streak",   "Streak keeper",   "7 days in a row",                  "fa-fire"),
    ("ten-sets",      "Curator",         "Built 10 study sets",              "fa-medal"),
]


def _achievement_state(user, sets_count):
    """Return list of dicts: {slug, title, blurb, icon, unlocked} in order."""
    unlocked_set = set()
    if sets_count >= 1:  unlocked_set.add("first-set")
    if sets_count >= 5:  unlocked_set.add("five-sets")
    if sets_count >= 10: unlocked_set.add("ten-sets")
    if user.streak and user.streak >= 7: unlocked_set.add("week-streak")
    return [
        {"slug": s, "title": t, "blurb": b, "icon": ic, "unlocked": s in unlocked_set}
        for (s, t, b, ic) in ACHIEVEMENTS
    ]


def _sanitize_avatar_emoji(raw):
    """Accept short non-ascii strings only. Reject typed text."""
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    # If it contains any letters/digits/whitespace, it's not an emoji.
    if any(ch.isascii() and (ch.isalnum() or ch.isspace()) for ch in s):
        return None
    return s[:8]


@main.route("/profile/avatar", methods=["POST"])
@login_required
def update_avatar():
    current_user.avatar_emoji = _sanitize_avatar_emoji(request.form.get("avatar_emoji"))
    db.session.commit()
    flash("Avatar updated." if current_user.avatar_emoji else "Avatar cleared.")
    return redirect(url_for("main.profile"))


@main.route("/profile")
@login_required
def profile():
    sets_count = len(current_user.study_sets)
    total_cards = sum(len(s.flashcards) for s in current_user.study_sets)

    sessions = (
        StudySession.query
        .filter_by(user_id=current_user.id)
        .order_by(StudySession.finished_at.desc())
        .all()
    )
    sessions_count = len(sessions)
    recent_sessions = sessions[:5]
    best_accuracy = max((s.accuracy for s in sessions), default=0.0)
    favorites_count = Favorite.query.filter_by(user_id=current_user.id).count()

    return render_template(
        "profile.html",
        total_cards=total_cards,
        sets_count=sets_count,
        sessions_count=sessions_count,
        best_accuracy=int(round(best_accuracy * 100)),
        favorites_count=favorites_count,
        achievements_state=_achievement_state(current_user, sets_count),
        recent_sessions=recent_sessions,
    )


@main.route("/search")
@login_required
def search_public_sets():
    query_text = request.args.get("q", "").strip()
    owner_text = request.args.get("owner", "").strip()

    search_query = StudySet.query.join(User).filter(StudySet.is_public.is_(True))
    if query_text:
        pattern = f"%{query_text}%"
        search_query = search_query.filter(
            or_(StudySet.title.ilike(pattern), StudySet.description.ilike(pattern))
        )
    if owner_text:
        search_query = search_query.filter(User.username.ilike(f"%{owner_text}%"))

    results = search_query.order_by(StudySet.id.desc()).limit(30).all()
    return render_template(
        "search.html",
        results=results,
        query_text=query_text,
        owner_text=owner_text,
    )


@main.route("/study-sets/<int:study_set_id>")
@login_required
def study_set_detail(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)
    recent_sessions = (
        StudySession.query
        .filter_by(study_set_id=study_set.id, user_id=current_user.id)
        .order_by(StudySession.finished_at.desc())
        .limit(8)
        .all()
    )
    return render_template(
        "study_set.html",
        study_set=study_set,
        recent_sessions=recent_sessions,
    )


@main.route("/study-sets/<int:study_set_id>/edit", methods=["GET", "POST"])
@login_required
def edit_study_set(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        is_public = request.form.get("is_public") == "on"

        flashcard_ids = request.form.getlist("flashcard_id")
        terms = request.form.getlist("term")
        definitions = request.form.getlist("definition")

        flashcard_rows = []
        for flashcard_id, term, definition in zip(flashcard_ids, terms, definitions):
            clean_term = term.strip()
            clean_definition = definition.strip()

            if not clean_term and not clean_definition:
                continue
            if not clean_term or not clean_definition:
                flash("Each flashcard must include both term and definition.")
                return render_template("edit_studyset.html", study_set=study_set), 400

            flashcard_rows.append((flashcard_id, clean_term, clean_definition))

        if not title:
            flash("Set title is required.")
            return render_template("edit_studyset.html", study_set=study_set), 400

        if not flashcard_rows:
            flash("Add at least one complete flashcard.")
            return render_template("edit_studyset.html", study_set=study_set), 400

        existing_flashcards = {str(card.id): card for card in study_set.flashcards}
        kept_flashcard_ids = set()

        for flashcard_id, term, definition in flashcard_rows:
            if flashcard_id:
                existing_flashcard = existing_flashcards.get(flashcard_id)
                if existing_flashcard is None:
                    continue
                existing_flashcard.question = term
                existing_flashcard.answer = definition
                kept_flashcard_ids.add(flashcard_id)
            else:
                db.session.add(
                    Flashcard(question=term, answer=definition, study_set=study_set)
                )

        for card_id, card in existing_flashcards.items():
            if card_id not in kept_flashcard_ids:
                db.session.delete(card)

        study_set.title = title
        study_set.description = description
        study_set.is_public = is_public
        db.session.commit()

        flash("Study set updated.")
        return redirect(url_for("main.study_set_detail", study_set_id=study_set.id))

    return render_template("edit_studyset.html", study_set=study_set)


@main.route("/study-sets/<int:study_set_id>/delete", methods=["POST"])
@login_required
def delete_study_set(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)
    db.session.delete(study_set)
    db.session.commit()
    flash("Study set deleted.")
    return redirect(url_for("main.study_sets"))


@main.route("/browse/study-sets/<int:study_set_id>")
@login_required
def browse_public_study_set(study_set_id):
    study_set = StudySet.query.filter_by(id=study_set_id, is_public=True).first()
    if study_set is None:
        abort(404)
    recent_sessions = (
        StudySession.query
        .filter_by(study_set_id=study_set.id, user_id=current_user.id)
        .order_by(StudySession.finished_at.desc())
        .limit(8)
        .all()
    )
    is_favorited = Favorite.query.filter_by(
        user_id=current_user.id, study_set_id=study_set.id
    ).first() is not None
    return render_template(
        "browse_study_set.html",
        study_set=study_set,
        recent_sessions=recent_sessions,
        is_favorited=is_favorited,
    )


@main.route("/study-sets/<int:study_set_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(study_set_id):
    study_set = get_playable_study_set_or_404(study_set_id)
    existing = Favorite.query.filter_by(
        user_id=current_user.id, study_set_id=study_set.id
    ).first()
    if existing:
        db.session.delete(existing)
        favorited = False
    else:
        db.session.add(Favorite(user_id=current_user.id, study_set_id=study_set.id))
        favorited = True
    db.session.commit()

    if request.is_json or "application/json" in (request.headers.get("Accept") or ""):
        return jsonify({"ok": True, "favorited": favorited})

    fallback = url_for("main.browse_public_study_set", study_set_id=study_set.id)
    return redirect(request.referrer or fallback)


@main.route("/favorites")
@login_required
def favorites():
    rows = (
        Favorite.query
        .filter_by(user_id=current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    # Hide sets that were unpublished by their owner (unless we own them).
    visible = [
        f.study_set for f in rows
        if f.study_set.is_public or f.study_set.user_id == current_user.id
    ]
    return render_template("favorites.html", study_sets=visible)


@main.route("/study-sets/<int:study_set_id>/study")
@login_required
def study_set_study(study_set_id):
    study_set = get_playable_study_set_or_404(study_set_id)
    return render_template(
        "study_mode.html",
        study_set=study_set,
        back_url=back_url_for_set(study_set),
    )


@main.route("/analytics")
@login_required
def analytics():
    user_study_sets = (
        StudySet.query.filter_by(user_id=current_user.id)
        .order_by(StudySet.id.desc())
        .all()
    )
    total_sets = len(user_study_sets)
    total_cards = sum(len(study_set.flashcards) for study_set in user_study_sets)
    public_sets = sum(1 for study_set in user_study_sets if study_set.is_public)
    average_cards = round(total_cards / total_sets, 1) if total_sets else 0

    recent_sets = user_study_sets[:7]
    raw_chart_values = [len(study_set.flashcards) for study_set in reversed(recent_sets)]
    chart_labels = [study_set.title[:10] for study_set in reversed(recent_sets)]
    if not raw_chart_values:
        raw_chart_values = [0]
        chart_labels = ["No sets"]

    max_value = max(raw_chart_values) or 1
    chart_data = [int((value / max_value) * 100) for value in raw_chart_values]

    return render_template(
        "analytics.html",
        total_cards=total_cards,
        total_sets=total_sets,
        public_sets=public_sets,
        average_cards=average_cards,
        chart_data=chart_data,
        chart_labels=chart_labels,
    )


MODE_CONFIG = {
    "flip": {
        "title": "Flip Mode",
        "tagline": "Step through your cards one at a time at your own pace.",
        "accent": "var(--accent)",
        "start_endpoint": "main.study_set_study",
        "cta": "Start flipping",
    },
    "quiz": {
        "title": "Quiz Mode",
        "tagline": "Multiple-choice questions drawn from your set.",
        "accent": "var(--accent-2)",
        "start_endpoint": "main.study_set_quiz",
        "cta": "Start quiz",
    },
    "time": {
        "title": "Time Game",
        "tagline": "Answer as many cards as you can in 60 seconds.",
        "accent": "#8c2d3a",
        "start_endpoint": "main.study_set_time",
        "cta": "Start the clock",
    },
}


@main.route("/study-sets/<int:study_set_id>/quiz")
@login_required
def study_set_quiz(study_set_id):
    study_set = get_playable_study_set_or_404(study_set_id)
    back_url = back_url_for_set(study_set)
    if not study_set.flashcards:
        flash("This set has no flashcards yet.")
        return redirect(back_url)
    return render_template("quiz_mode.html", study_set=study_set, back_url=back_url)


@main.route("/study-sets/<int:study_set_id>/time")
@login_required
def study_set_time(study_set_id):
    study_set = get_playable_study_set_or_404(study_set_id)
    back_url = back_url_for_set(study_set)
    if len(study_set.flashcards) < 2:
        flash("Time Game needs at least two flashcards.")
        return redirect(back_url)
    return render_template("time_mode.html", study_set=study_set, back_url=back_url)


def _record_session(study_set, mode, score, total):
    accuracy = (score / total) if total > 0 else 0.0
    session = StudySession(
        user_id=current_user.id,
        study_set_id=study_set.id,
        mode=mode,
        score=score,
        total=total,
        accuracy=accuracy,
    )
    db.session.add(session)
    db.session.commit()
    return session


def _parse_int(payload, key):
    try:
        return int(payload.get(key, 0))
    except (TypeError, ValueError):
        return None


@main.route("/study-sets/<int:study_set_id>/quiz/submit", methods=["POST"])
@login_required
def submit_quiz_session(study_set_id):
    study_set = get_playable_study_set_or_404(study_set_id)
    payload = request.get_json(silent=True) or {}

    score = _parse_int(payload, "score")
    total = _parse_int(payload, "total")
    if score is None or total is None or total <= 0 or score < 0 or score > total:
        return jsonify({"ok": False, "error": "invalid score / total"}), 400

    session = _record_session(study_set, "quiz", score, total)
    return jsonify({
        "ok": True,
        "session_id": session.id,
        "accuracy": round(session.accuracy, 3),
    })


@main.route("/study-sets/<int:study_set_id>/time/submit", methods=["POST"])
@login_required
def submit_time_session(study_set_id):
    study_set = get_playable_study_set_or_404(study_set_id)
    payload = request.get_json(silent=True) or {}

    right = _parse_int(payload, "right")
    wrong = _parse_int(payload, "wrong")
    if right is None or wrong is None or right < 0 or wrong < 0:
        return jsonify({"ok": False, "error": "invalid right / wrong counts"}), 400

    total = right + wrong
    if total == 0:
        return jsonify({"ok": False, "error": "no answers recorded"}), 400

    session = _record_session(study_set, "time", right, total)
    return jsonify({
        "ok": True,
        "session_id": session.id,
        "accuracy": round(session.accuracy, 3),
    })


STATIC_PAGES = [
    ("Dashboard",          "main.index",              "fa-house"),
    ("My study sets",      "main.study_sets",         "fa-book"),
    ("Search public sets", "main.search_public_sets", "fa-magnifying-glass"),
    ("Create new set",     "main.create_study_set",   "fa-plus"),
    ("Favorites",          "main.favorites",          "fa-heart"),
    ("Analytics",          "main.analytics",          "fa-chart-bar"),
    ("Settings",           "main.settings",           "fa-gear"),
    ("Profile",            "main.profile",            "fa-user"),
]


def _safe_emoji(s):
    """Return s only if it looks like an emoji; otherwise None."""
    if not s:
        return None
    if any(c.isascii() and (c.isalnum() or c.isspace()) for c in s):
        return None
    return s


@main.route("/api/search")
@login_required
def api_search():
    """Quick site-wide search used by the header bar.

    Returns up to ~25 results grouped by type. Pages first, then sets,
    then individual cards / tags. Each result has the same shape so the
    client can render them uniformly.
    """
    q = (request.args.get("q") or "").strip()
    results = []

    # Static pages — match anytime, even on a single char.
    if q:
        ql = q.lower()
        for label, endpoint, icon in STATIC_PAGES:
            if ql in label.lower():
                results.append({
                    "type": "page",
                    "title": label,
                    "subtitle": "Page",
                    "url": url_for(endpoint),
                    "icon": icon,
                })

    # The rest need at least two characters before we hit the DB.
    if len(q) >= 2:
        pat = f"%{q}%"

        own = (
            StudySet.query
            .filter(StudySet.user_id == current_user.id)
            .filter(or_(StudySet.title.ilike(pat), StudySet.description.ilike(pat)))
            .limit(5).all()
        )
        for s in own:
            results.append({
                "type": "set",
                "title": s.title,
                "subtitle": f"Your set · {len(s.flashcards)} card{'s' if len(s.flashcards) != 1 else ''}",
                "url": url_for("main.study_set_detail", study_set_id=s.id),
                "icon": "fa-book",
                "emoji": _safe_emoji(s.cover_emoji),
            })

        pub = (
            StudySet.query
            .filter(StudySet.user_id != current_user.id, StudySet.is_public == True)
            .filter(or_(StudySet.title.ilike(pat), StudySet.description.ilike(pat)))
            .limit(5).all()
        )
        for s in pub:
            results.append({
                "type": "public",
                "title": s.title,
                "subtitle": f"Public · by {s.owner.username}",
                "url": url_for("main.browse_public_study_set", study_set_id=s.id),
                "icon": "fa-users",
                "emoji": _safe_emoji(s.cover_emoji),
            })

        tags = Tag.query.filter(Tag.name.ilike(pat)).limit(4).all()
        for t in tags:
            results.append({
                "type": "tag",
                "title": "#" + t.name,
                "subtitle": f"Tag · {len(t.study_sets)} set{'s' if len(t.study_sets) != 1 else ''}",
                "url": url_for("main.search_public_sets", q=t.name),
                "icon": "fa-tag",
            })

        cards = (
            Flashcard.query.join(StudySet)
            .filter(or_(
                StudySet.user_id == current_user.id,
                StudySet.is_public == True,
            ))
            .filter(or_(Flashcard.question.ilike(pat), Flashcard.answer.ilike(pat)))
            .limit(6).all()
        )
        for c in cards:
            results.append({
                "type": "card",
                "title": (c.question or "")[:80],
                "subtitle": f"Card in {c.study_set.title}",
                "url": (
                    url_for("main.study_set_detail", study_set_id=c.study_set_id)
                    if c.study_set.user_id == current_user.id
                    else url_for("main.browse_public_study_set", study_set_id=c.study_set_id)
                ),
                "icon": "fa-rectangle-list",
            })

    return jsonify({"q": q, "results": results})


@main.route("/modes/<mode>")
@login_required
def mode_select(mode):
    if mode not in MODE_CONFIG:
        abort(404)

    user_study_sets = (
        StudySet.query.filter_by(user_id=current_user.id)
        .order_by(StudySet.id.desc())
        .all()
    )

    return render_template(
        "mode_select.html",
        mode=mode,
        config=MODE_CONFIG[mode],
        study_sets=user_study_sets,
    )