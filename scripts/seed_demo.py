"""Load demo data: python scripts/seed_demo.py from project root."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Card, StudySet, User


def main() -> None:
    app = create_app()
    with app.app_context():
        email = "demo@example.com"
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(email=email, full_name="Lynn Ta", title="Medical student")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
        sets_data = [
            ("History", "Important events in world history", True, [("Year 1066", "Battle of Hastings", ["1066", "1215", "1492", "1776"])]),
            (
                "Programming",
                "Essential Python concepts",
                True,
                [
                    ("Why use a for loop in Python?", "To iterate over a sequence", ["To iterate over a sequence", "To stop the program", "To declare types", "To import modules"]),
                    ("Why use a while loop?", "While a condition is true", ["While a condition is true", "Only once", "Never", "For imports"]),
                ],
            ),
            ("Python Logic", "Covers range of topic in Python", False, [("What is a list?", "Ordered collection", ["Ordered collection", "Unordered", "Fixed size only", "Not in Python"])]),
        ]
        for title, desc, public, cards in sets_data:
            existing = StudySet.query.filter_by(user_id=u.id, title=title).first()
            if existing:
                continue
            s = StudySet(user_id=u.id, title=title, description=desc, is_public=public)
            db.session.add(s)
            db.session.flush()
            for term, definition, opts in cards:
                oa, ob, oc, od = opts[0], opts[1], opts[2], opts[3]
                ci = 0
                for i, t in enumerate([oa, ob, oc, od]):
                    if t == definition:
                        ci = i
                        break
                db.session.add(
                    Card(
                        study_set_id=s.id,
                        term=term,
                        definition=definition,
                        option_a=oa,
                        option_b=ob,
                        option_c=oc,
                        option_d=od,
                        correct_index=ci,
                    )
                )
            db.session.commit()
        print("Seed complete. Login:", email, "/ password123")


if __name__ == "__main__":
    main()
