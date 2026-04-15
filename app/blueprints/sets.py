from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from app.decorators import current_user_id, login_required
from app.extensions import db
from app.models import Card, StudyProgress, StudySet, difficulty_counts_for_set

sets_bp = Blueprint("sets", __name__, url_prefix="/sets")


def _get_owned_set(set_id: int, user_id: int) -> StudySet:
    s = StudySet.query.filter_by(id=set_id, user_id=user_id).first()
    if not s:
        abort(404)
    return s


@sets_bp.route("/my")
@login_required
def my_sets():
    uid = current_user_id()
    assert uid is not None
    items = StudySet.query.filter_by(user_id=uid).order_by(StudySet.updated_at.desc(), StudySet.id.desc()).all()
    return render_template("sets/my_sets.html", sets=items)


@sets_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    uid = current_user_id()
    assert uid is not None
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        if not title:
            flash("Set title is required.", "error")
            return render_template("sets/create.html", title=title, description=description)
        s = StudySet(user_id=uid, title=title, description=description or None)
        db.session.add(s)
        db.session.flush()
        _upsert_cards_from_form(s.id, request.form)
        db.session.commit()
        flash("Study set created.", "success")
        return redirect(url_for("sets.my_sets"))
    return render_template("sets/create.html")


@sets_bp.route("/<int:set_id>/edit", methods=["GET", "POST"])
@login_required
def edit(set_id: int):
    uid = current_user_id()
    assert uid is not None
    s = _get_owned_set(set_id, uid)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        if not title:
            flash("Set title is required.", "error")
            return render_template("sets/edit.html", study_set=s, cards=s.cards.all())
        s.title = title
        s.description = description or None
        Card.query.filter_by(study_set_id=s.id).delete()
        _upsert_cards_from_form(s.id, request.form)
        db.session.commit()
        flash("Changes saved.", "success")
        return redirect(url_for("sets.my_sets"))
    return render_template("sets/edit.html", study_set=s, cards=s.cards.all())


def _upsert_cards_from_form(study_set_id: int, form) -> None:
    """Read dynamic question indices from form: term_1, def_1, opt_1_0, etc."""
    indices: set[int] = set()
    for key in form.keys():
        if key.startswith("term_"):
            try:
                indices.add(int(key.split("_", 1)[1]))
            except ValueError:
                pass
    for i in sorted(indices):
        term = (form.get(f"term_{i}") or "").strip()
        definition = (form.get(f"def_{i}") or "").strip()
        if not term and not definition:
            continue
        oa = (form.get(f"opt_{i}_0") or "").strip()
        ob = (form.get(f"opt_{i}_1") or "").strip()
        oc = (form.get(f"opt_{i}_2") or "").strip()
        od = (form.get(f"opt_{i}_3") or "").strip()
        if not oa:
            oa = definition or term
        if not ob:
            ob = definition or "Option B"
        if not oc:
            oc = "Option C"
        if not od:
            od = "Option D"
        correct_index = 0
        for idx, val in enumerate([oa, ob, oc, od]):
            if val.strip() == definition.strip():
                correct_index = idx
                break
        c = Card(
            study_set_id=study_set_id,
            term=term or "Untitled",
            definition=definition or "",
            option_a=oa,
            option_b=ob,
            option_c=oc,
            option_d=od,
            correct_index=correct_index,
        )
        db.session.add(c)


@sets_bp.route("/<int:set_id>/delete", methods=["POST"])
@login_required
def delete_set(set_id: int):
    uid = current_user_id()
    assert uid is not None
    s = _get_owned_set(set_id, uid)
    db.session.delete(s)
    db.session.commit()
    flash("Study set deleted.", "success")
    return redirect(url_for("sets.my_sets"))


@sets_bp.route("/<int:set_id>/toggle-public", methods=["POST"])
@login_required
def toggle_public(set_id: int):
    uid = current_user_id()
    assert uid is not None
    s = _get_owned_set(set_id, uid)
    s.is_public = not s.is_public
    db.session.commit()
    return redirect(request.referrer or url_for("sets.my_sets"))


@sets_bp.route("/<int:set_id>")
@login_required
def set_overview(set_id: int):
    uid = current_user_id()
    assert uid is not None
    s = StudySet.query.get_or_404(set_id)
    if s.user_id != uid and not s.is_public:
        abort(403)
    counts = difficulty_counts_for_set(uid, set_id) if s.user_id == uid else {"easy": 0, "medium": 0, "hard": 0}
    if s.user_id != uid:
        # viewer: no personal difficulty breakdown
        counts = {"easy": 0, "medium": 0, "hard": 0}
    n = s.cards.count()
    return render_template("sets/overview.html", study_set=s, counts=counts, card_count=n)


@sets_bp.route("/<int:set_id>/review")
@login_required
def review_modes(set_id: int):
    uid = current_user_id()
    assert uid is not None
    s = StudySet.query.get_or_404(set_id)
    if s.user_id != uid and not s.is_public:
        abort(403)
    if s.cards.count() == 0:
        flash("This set has no cards yet.", "error")
        return redirect(url_for("sets.set_overview", set_id=set_id))
    return render_template("study/review_modes.html", study_set=s)


def _cards_payload(study_set: StudySet) -> list[dict]:
    out = []
    for c in study_set.cards.order_by(Card.id).all():
        out.append(
            {
                "id": c.id,
                "term": c.term,
                "definition": c.definition,
                "options": c.options_list(),
                "correct_index": c.correct_index,
            }
        )
    return out


@sets_bp.route("/<int:set_id>/flip")
@login_required
def flip(set_id: int):
    uid = current_user_id()
    assert uid is not None
    s = StudySet.query.get_or_404(set_id)
    if s.user_id != uid and not s.is_public:
        abort(403)
    cards = _cards_payload(s)
    if not cards:
        flash("No cards in this set.", "error")
        return redirect(url_for("sets.set_overview", set_id=set_id))
    return render_template(
        "study/flip.html",
        study_set=s,
        cards=cards,
    )


@sets_bp.route("/<int:set_id>/quiz")
@login_required
def quiz(set_id: int):
    uid = current_user_id()
    assert uid is not None
    timed = request.args.get("timed") == "1"
    s = StudySet.query.get_or_404(set_id)
    if s.user_id != uid and not s.is_public:
        abort(403)
    cards = _cards_payload(s)
    if not cards:
        flash("No cards in this set.", "error")
        return redirect(url_for("sets.set_overview", set_id=set_id))
    return render_template(
        "study/quiz.html",
        study_set=s,
        cards=cards,
        timed=timed,
        timed_seconds=60,
    )
