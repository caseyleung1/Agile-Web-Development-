"""Seed the database with a large demo dataset for showcase purposes.

Usage:
    python seed.py             # add demo data (skip anything that already exists)
    python seed.py --reset     # wipe existing data first, then seed fresh

After seeding, log in with any listed account (password is always <username>1234)
or the legacy demo accounts below.
"""
import random
import sys
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import (
    Favorite,
    Flashcard,
    StudySession,
    StudySet,
    Tag,
    User,
    study_set_tag,
)

random.seed(42)

# Legacy accounts referenced in README — always created with these passwords.
CORE_USERS = [
    {"username": "demo", "email": "demo@uwa.edu.au", "password": "demo1234"},
    {"username": "alice", "email": "alice@student.uwa.edu.au", "password": "alice1234"},
    {"username": "sam", "email": "sam@student.uwa.edu.au", "password": "sam1234"},
]

FIRST_NAMES = [
    "alex", "blake", "casey", "dana", "elliot", "finn", "gray", "harper",
    "ivy", "jordan", "kai", "logan", "maya", "noah", "olivia", "parker",
    "quinn", "riley", "sage", "taylor", "uma", "vale", "wren", "xander",
    "yuki", "zara", "aaron", "bella", "cameron", "devon", "eden", "frankie",
    "george", "hannah", "isla", "jamie", "kate", "liam", "morgan", "nia",
    "owen", "piper", "reese", "skylar", "tessa", "uma", "victor", "willow",
]

LAST_NAMES = [
    "nguyen", "patel", "smith", "chen", "kim", "garcia", "lee", "brown",
    "wilson", "martin", "kumar", "singh", "wang", "ali", "murphy", "khan",
    "robinson", "clark", "wright", "hall", "young", "king", "scott", "adams",
]

AVATAR_EMOJIS = ["📘", "🧠", "🧪", "🌍", "🔢", "🎨", "🎵", "💻", "📚", "✏️", "🧬", "🗺️", "⚽", "🍎", "🎬", "⚙️", "🚀", "💡", "🔬", "🎯", "🌿", "🏛️", "🩺", "⚖️", "🦴", "🧮", "🖥️", "📝", "🌸", "🐾", "🏥", "📊", "🎓", "🔭", "🧘", "🍳", "🚗", "🌊", "🏗️", "🎸", "📐", "🧲", "🦠", "🌙", "☀️", "🌋", "🎭", "🏃", "🧑‍💻", "👩‍🔬", "🧑‍🏫"]

COVER_EMOJIS = ["📘", "🧠", "🧪", "🌍", "🔢", "🎨", "🎵", "💻", "📚", "✏️", "🧬", "🗺️", "⚽", "🍎", "🎬", "⚙️", "🚀", "💡", "🔬", "🎯"]

TAG_POOL = [
    "exam-prep", "uwa", "cits3403", "year-1", "year-2", "year-3", "revision",
    "python", "javascript", "web-dev", "databases", "algorithms", "networking",
    "biology", "chemistry", "physics", "anatomy", "nursing", "medicine",
    "spanish", "french", "japanese", "languages", "vocabulary", "grammar",
    "history", "ancient-history", "world-war", "australia", "europe",
    "calculus", "statistics", "linear-algebra", "discrete-math",
    "business", "accounting", "marketing", "law", "ethics",
    "public", "community", "beginner", "advanced", "cheatsheet", "lab",
]

# Rich card banks per subject — each entry is (question, answer).
CARD_BANKS = {
    "python": [
        ("What does len() return for a string?", "The number of characters in the string."),
        ("How do you create an empty dictionary?", "Use {} or dict()."),
        ("What is a list comprehension?", "A concise way to build a list, e.g. [x*2 for x in nums]."),
        ("What does the 'is' operator check?", "Whether two references point to the same object."),
        ("How do you open a file safely?", "Use a with statement: with open(path) as f: ..."),
        ("What is a tuple?", "An immutable ordered collection of values."),
        ("How do you swap two variables?", "a, b = b, a"),
        ("What does .strip() do on a string?", "Removes leading and trailing whitespace."),
        ("What is a generator?", "A function that yields values lazily using yield."),
        ("What does *args collect?", "Extra positional arguments as a tuple."),
        ("What does **kwargs collect?", "Extra keyword arguments as a dictionary."),
        ("How do you catch exceptions?", "try: ... except SomeError: ..."),
        ("What is None in Python?", "A singleton representing the absence of a value."),
        ("What does import math as m do?", "Imports the math module under the alias m."),
        ("What is slicing s[1:4]?", "Characters at indices 1, 2, and 3."),
        ("What does enumerate() return?", "Pairs of (index, item) while iterating."),
        ("What is a set useful for?", "Storing unique elements with fast membership tests."),
        ("What does dict.get(key, default) do?", "Returns the value or default if the key is missing."),
        ("What is the GIL?", "Global Interpreter Lock — one thread executes Python bytecode at a time in CPython."),
        ("What does pip install do?", "Downloads and installs packages from PyPI."),
        ("What is __name__ == '__main__' used for?", "Guards code that should run only when the file is executed directly."),
    ],
    "web": [
        ("What does HTTP stand for?", "HyperText Transfer Protocol."),
        ("What is CORS?", "Cross-Origin Resource Sharing — browser policy for cross-origin requests."),
        ("HTTP status 404 means?", "Not Found."),
        ("HTTP status 500 means?", "Internal Server Error."),
        ("What is the DOM?", "Document Object Model — a tree representation of an HTML document."),
        ("What does REST stand for?", "Representational State Transfer."),
        ("Difference between PUT and PATCH?", "PUT replaces the whole resource; PATCH updates part of it."),
        ("What is a CDN?", "Content Delivery Network — distributed caches for static assets."),
        ("What is HTML semantic markup?", "Using elements that describe meaning, e.g. <article>, <nav>."),
        ("What does CSS specificity determine?", "Which rule wins when selectors conflict."),
        ("What is the box model?", "content → padding → border → margin."),
        ("What does display: flex do?", "Enables a flex formatting context for children."),
        ("What is localStorage?", "Browser key-value storage that persists across sessions."),
        ("What is a JWT?", "JSON Web Token — a signed token often used for stateless auth."),
        ("What does async/await do in JS?", "Syntactic sugar over Promises for asynchronous code."),
        ("What is SQL injection?", "Attacking an app by inserting malicious SQL via user input."),
        ("What is XSS?", "Cross-Site Scripting — injecting scripts into pages viewed by others."),
        ("What does SameSite=Lax on a cookie do?", "Limits cross-site cookie sending on top-level navigations."),
        ("What is WebSocket used for?", "Full-duplex communication over a single TCP connection."),
        ("What is responsive design?", "Layouts that adapt to different screen sizes."),
        ("What does aria-label provide?", "An accessible name for assistive technologies."),
    ],
    "algorithms": [
        ("Average lookup in a hash table?", "O(1) expected."),
        ("Worst-case search in unsorted array?", "O(n)."),
        ("Binary search time complexity?", "O(log n)."),
        ("Merge sort time complexity?", "O(n log n)."),
        ("Quick sort average case?", "O(n log n)."),
        ("BFS uses which data structure?", "A queue."),
        ("DFS uses which data structure?", "A stack (or recursion)."),
        ("Dijkstra's algorithm finds?", "Shortest paths from a source in weighted graphs."),
        ("What is dynamic programming?", "Breaking problems into overlapping subproblems with memoization."),
        ("What is a greedy algorithm?", "Makes locally optimal choices at each step."),
        ("Stable sorting means?", "Equal elements keep their relative order."),
        ("What is amortized O(1)?", "Average O(1) per operation over a sequence."),
        ("Heap extract-min time?", "O(log n)."),
        ("What is NP-complete?", "A class of problems at least as hard as the hardest in NP."),
        ("Two-pointer technique requires?", "Often a sorted array or list."),
        ("Sliding window helps with?", "Subarray/substring problems in linear time."),
    ],
    "databases": [
        ("INNER JOIN returns?", "Rows matching in both tables."),
        ("LEFT JOIN returns?", "All left rows; NULL on the right when no match."),
        ("What is a primary key?", "Uniquely identifies each row in a table."),
        ("What is a foreign key?", "References a primary key in another table."),
        ("ACID stands for?", "Atomicity, Consistency, Isolation, Durability."),
        ("What is normalization?", "Organizing data to reduce redundancy."),
        ("What is an index used for?", "Speeding up lookups at the cost of write overhead."),
        ("Difference between WHERE and HAVING?", "WHERE filters rows; HAVING filters groups."),
        ("What is a transaction?", "A group of operations committed or rolled back together."),
        ("What does GROUP BY do?", "Aggregates rows sharing the same column values."),
        ("What is a view?", "A stored query treated like a virtual table."),
        ("NoSQL often trades what for scale?", "Flexible schema and horizontal scaling vs strict relational guarantees."),
        ("What is a composite index?", "An index on multiple columns together."),
        ("What is connection pooling?", "Reusing DB connections instead of opening new ones per request."),
    ],
    "biology": [
        ("Powerhouse of the cell?", "Mitochondria."),
        ("Site of protein synthesis?", "Ribosomes (rough ER has bound ribosomes)."),
        ("Molecule that stores genetic information?", "DNA."),
        ("Process plants use to make glucose?", "Photosynthesis."),
        ("Basic unit of life?", "The cell."),
        ("Organelle that packages proteins?", "Golgi apparatus."),
        ("Process of cell division producing identical cells?", "Mitosis."),
        ("Gametes are produced by?", "Meiosis."),
        ("Fluid mosaic model describes?", "The cell membrane structure."),
        ("Enzymes are a type of?", "Protein (usually) that catalyzes reactions."),
        ("ATP stands for?", "Adenosine triphosphate."),
        ("Central dogma: DNA → ?", "RNA → protein."),
        ("Antibodies are produced by?", "B lymphocytes (B cells)."),
        ("Homeostasis means?", "Maintaining stable internal conditions."),
        ("Osmosis is movement of?", "Water across a semipermeable membrane."),
    ],
    "anatomy": [
        ("Largest bone in the body?", "Femur."),
        ("Adult human bone count?", "206."),
        ("Collarbone is also called?", "Clavicle."),
        ("Kneecap is also called?", "Patella."),
        ("Smallest bone in the body?", "Stapes (middle ear)."),
        ("Wrist bones collectively?", "Carpals."),
        ("Number of cervical vertebrae?", "Seven."),
        ("Shoulder blade?", "Scapula."),
        ("Thumb-side forearm bone?", "Radius."),
        ("Ribs attach anteriorly to?", "Sternum."),
        ("Heart has how many chambers?", "Four."),
        ("Largest organ by surface area?", "Skin."),
        ("Longest nerve in the body?", "Sciatic nerve."),
    ],
    "chemistry": [
        ("Atomic number equals?", "Number of protons."),
        ("pH 7 is?", "Neutral."),
        ("Avogadro's number is about?", "6.022 × 10²³ particles per mole."),
        ("Covalent bond involves?", "Sharing electron pairs."),
        ("Ionic bond involves?", "Transfer of electrons between atoms."),
        ("Exothermic reaction?", "Releases heat to surroundings."),
        ("Catalyst does what?", "Speeds a reaction without being consumed."),
        ("Oxidation involves?", "Loss of electrons (LEO says GER)."),
        ("Molarity units?", "mol/L."),
        ("Ideal gas law?", "PV = nRT."),
        ("Alkane general formula?", "CₙH₂ₙ₊₂."),
        ("Strongest intermolecular force in water?", "Hydrogen bonding."),
    ],
    "spanish": [
        ("ser", "to be (permanent)"),
        ("estar", "to be (temporary/location)"),
        ("tener", "to have"),
        ("hacer", "to do / make"),
        ("ir", "to go"),
        ("poder", "can / to be able to"),
        ("decir", "to say / tell"),
        ("ver", "to see"),
        ("venir", "to come"),
        ("saber", "to know (facts)"),
        ("conocer", "to know (people/places)"),
        ("querer", "to want"),
        ("llegar", "to arrive"),
        ("hablar", "to speak"),
        ("comer", "to eat"),
    ],
    "japanese": [
        ("Ohayou gozaimasu", "Good morning (polite)"),
        ("Konnichiwa", "Hello / Good afternoon"),
        ("Konbanwa", "Good evening"),
        ("Arigatou gozaimasu", "Thank you (polite)"),
        ("Sumimasen", "Excuse me / Sorry"),
        ("Hajimemashite", "Nice to meet you"),
        ("Hai", "Yes"),
        ("Iie", "No"),
        ("Wakarimashita", "I understood"),
        ("Onegaishimasu", "Please (request)"),
        ("Gomen nasai", "I'm sorry"),
        ("Itadakimasu", "Said before eating"),
        ("Sayounara", "Goodbye"),
    ],
    "history": [
        ("Rome traditionally founded?", "753 BCE."),
        ("First Roman emperor?", "Augustus."),
        ("Western Roman Empire fell?", "476 CE."),
        ("Who crossed the Rubicon?", "Julius Caesar (49 BCE)."),
        ("Pax Romana was?", "~200 years of relative peace in the empire."),
        ("Pearl Harbor attack date?", "7 December 1941."),
        ("Battle of Midway year?", "1942."),
        ("Japan surrendered?", "2 September 1945."),
        ("Magna Carta signed?", "1215."),
        ("French Revolution began?", "1789."),
        ("First moon landing year?", "1969."),
        ("Berlin Wall fell?", "1989."),
    ],
    "math": [
        ("Derivative of x²?", "2x."),
        ("Integral of 1/x dx?", "ln|x| + C."),
        ("Pythagorean theorem?", "a² + b² = c² for a right triangle."),
        ("sin²θ + cos²θ equals?", "1."),
        ("Determinant of 2×2 [[a,b],[c,d]]?", "ad − bc."),
        ("Euclidean algorithm finds?", "GCD of two integers."),
        ("Bayes' theorem updates?", "Prior probability with evidence."),
        ("Mean of [1,2,3,4,5]?", "3."),
        ("Variance measures?", "Spread around the mean."),
        ("e ≈ ?", "2.71828..."),
        ("π ≈ ?", "3.14159..."),
        ("log₁₀(1000)?", "3."),
        ("Factorial 5?", "120."),
        ("Sum of first n integers?", "n(n+1)/2."),
    ],
    "nursing": [
        ("Normal adult resting heart rate (bpm)?", "60–100."),
        ("Normal adult respiratory rate?", "12–20 breaths per minute."),
        ("AVPU scale assesses?", "Alert, Voice, Pain, Unresponsive."),
        ("SBAR stands for?", "Situation, Background, Assessment, Recommendation."),
        ("Signs vs symptoms?", "Signs are observable; symptoms are reported by the patient."),
        ("Hand hygiene: alcohol rub until?", "Hands are dry."),
        ("Orthostatic BP check timing?", "1 and 3 minutes after standing."),
        ("Parkland formula estimates?", "Fluid resuscitation for burn patients."),
        ("Five rights of medication?", "Right patient, drug, dose, route, time."),
        ("NPO means?", "Nothing by mouth."),
        ("DVT prevention includes?", "Mobility, compression, anticoagulation when indicated."),
    ],
    "law": [
        ("Burden of proof in criminal trial?", "Prosecution — beyond reasonable doubt."),
        ("Tort law deals with?", "Civil wrongs causing harm."),
        ("Stare decisis means?", "Stand by things decided — precedent."),
        ("Habeas corpus protects?", "Freedom from unlawful detention."),
        ("Contract requires?", "Offer, acceptance, consideration, intention."),
        ("Negligence elements?", "Duty, breach, causation, damage."),
        ("Ultra vires means?", "Beyond legal powers."),
        ("Ratio decidendi is?", "The legal reasoning binding in a case."),
        ("Obiter dicta are?", "Non-binding comments by a judge."),
        ("Statute of limitations?", "Time limit to bring legal action."),
    ],
}

SET_TEMPLATES = [
    ("python", "Python Fundamentals", "Core syntax, types, and everyday idioms.", True),
    ("python", "Python Advanced", "Generators, decorators, and modules.", False),
    ("web", "Web Development Essentials", "HTTP, HTML, CSS, and browser APIs.", True),
    ("web", "Web Security Basics", "Auth, cookies, and common vulnerabilities.", True),
    ("algorithms", "Algorithms & Complexity", "Big-O, classic algorithms, and patterns.", True),
    ("algorithms", "Interview Algorithms", "BFS, DFS, DP, and two-pointer tricks.", True),
    ("databases", "SQL & Relational DBs", "Joins, keys, and transactions.", True),
    ("databases", "Database Design", "Normalization, indexes, and modeling.", False),
    ("biology", "Cell Biology", "Organelles, metabolism, and the central dogma.", True),
    ("biology", "Molecular Biology", "DNA, RNA, proteins, and enzymes.", True),
    ("anatomy", "Human Anatomy: Bones", "Axial and appendicular skeleton.", True),
    ("anatomy", "Cardiovascular System", "Heart, vessels, and circulation.", True),
    ("chemistry", "General Chemistry", "Atoms, bonding, and reactions.", True),
    ("chemistry", "Organic Chemistry Intro", "Functional groups and nomenclature.", False),
    ("spanish", "Spanish Verbs", "High-frequency verbs and meanings.", True),
    ("spanish", "Spanish Phrases", "Everyday conversation.", True),
    ("japanese", "Japanese Greetings", "Polite everyday phrases.", True),
    ("japanese", "Japanese Numbers", "Counting and basic numerals.", True),
    ("history", "Ancient Rome", "Republic, empire, and legacy.", True),
    ("history", "World War II", "Key events and turning points.", True),
    ("math", "Calculus Review", "Derivatives, integrals, and identities.", True),
    ("math", "Statistics Essentials", "Mean, variance, and probability.", True),
    ("nursing", "Nursing Fundamentals", "Vitals, assessment, and safety.", True),
    ("nursing", "Clinical Skills", "Documentation and handover.", False),
    ("law", "Introduction to Law", "Courts, precedent, and legal reasoning.", True),
    ("law", "Contract Law Basics", "Formation and breach.", False),
]

TARGET_USER_COUNT = 50


def _build_usernames():
    """~50 unique usernames from name parts, plus core accounts."""
    names = set(u["username"] for u in CORE_USERS)
    candidates = []
    for first in FIRST_NAMES:
        for last in LAST_NAMES:
            candidates.append(f"{first}{last[0]}")
            candidates.append(f"{first}_{last}")
            if len(candidates) >= TARGET_USER_COUNT:
                break
        if len(candidates) >= TARGET_USER_COUNT:
            break
    random.shuffle(candidates)
    for c in candidates:
        if c not in names:
            names.add(c)
        if len(names) >= TARGET_USER_COUNT:
            break
    # Fill gaps with numbered variants if needed
    i = 1
    while len(names) < TARGET_USER_COUNT:
        names.add(f"student{i:02d}")
        i += 1
    return list(names)[:TARGET_USER_COUNT]


def _user_specs():
    specs = list(CORE_USERS)
    core_names = {u["username"] for u in CORE_USERS}
    for username in _build_usernames():
        if username in core_names:
            continue
        specs.append({
            "username": username,
            "email": f"{username}@student.uwa.edu.au",
            "password": f"{username}1234",
        })
    return specs


def _pick_cards(bank_key, count):
    bank = CARD_BANKS[bank_key]
    if count <= len(bank):
        return random.sample(bank, count)
    # Repeat with slight variation labels if we need more than the bank has
    cards = list(bank)
    while len(cards) < count:
        q, a = random.choice(bank)
        cards.append((f"{q} (review {len(cards)+1})", a))
    return cards[:count]


def _assign_tags(study_set, tag_objects):
    n = random.randint(2, 5)
    chosen = random.sample(tag_objects, min(n, len(tag_objects)))
    study_set.tags = chosen


def _wipe_all():
    print("→ Wiping existing data...")
    StudySession.query.delete()
    Favorite.query.delete()
    Flashcard.query.delete()
    db.session.execute(study_set_tag.delete())
    StudySet.query.delete()
    Tag.query.delete()
    User.query.delete()
    db.session.commit()


def seed():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            _wipe_all()

        user_specs = _user_specs()
        users_by_name = {}
        created_users = 0

        for i, spec in enumerate(user_specs):
            existing = User.query.filter_by(username=spec["username"]).first()
            if existing:
                users_by_name[spec["username"]] = existing
                continue
            days_ago = random.randint(0, 45)
            user = User(
                username=spec["username"],
                email=spec["email"],
                streak=random.randint(0, min(45, 30 + (i % 15))),
                achievements=random.randint(0, 4),
                last_active=datetime.now(timezone.utc) - timedelta(days=days_ago),
                avatar_emoji=random.choice(AVATAR_EMOJIS) if random.random() < 0.85 else None,
            )
            user.set_password(spec["password"])
            db.session.add(user)
            users_by_name[spec["username"]] = user
            created_users += 1

        db.session.commit()
        # Refresh IDs for users created in this batch
        for spec in user_specs:
            users_by_name[spec["username"]] = User.query.filter_by(username=spec["username"]).first()

        tag_objects = []
        for name in TAG_POOL:
            tag = Tag.get_or_create(name)
            if tag:
                tag_objects.append(tag)
        db.session.commit()

        all_sets = []
        created_sets = 0
        usernames = list(users_by_name.keys())
        random.shuffle(usernames)

        # Each user gets 4–9 study sets from shuffled templates
        template_pool = list(SET_TEMPLATES)
        random.shuffle(template_pool)
        template_idx = 0

        for username in usernames:
            owner = users_by_name[username]
            n_sets = random.randint(4, 9)
            for _ in range(n_sets):
                bank_key, title, desc, default_public = template_pool[template_idx % len(template_pool)]
                template_idx += 1
                # Avoid exact duplicate title per owner
                suffix = ""
                final_title = title + suffix
                attempt = 0
                while StudySet.query.filter_by(title=final_title, user_id=owner.id).first():
                    attempt += 1
                    final_title = f"{title} ({attempt})"

                is_public = default_public if random.random() < 0.75 else not default_public
                card_count = random.randint(12, min(28, len(CARD_BANKS[bank_key]) + 5))
                cards = _pick_cards(bank_key, card_count)

                study_set = StudySet(
                    title=final_title,
                    description=desc,
                    is_public=is_public,
                    cover_emoji=random.choice(COVER_EMOJIS) if random.random() < 0.7 else None,
                    owner=owner,
                    flashcards=[Flashcard(question=q, answer=a) for q, a in cards],
                )
                _assign_tags(study_set, tag_objects)
                db.session.add(study_set)
                all_sets.append(study_set)
                created_sets += 1

        db.session.commit()

        # Refresh study sets with IDs
        all_sets = StudySet.query.all()
        public_sets = [s for s in all_sets if s.is_public]
        users = list(users_by_name.values())

        created_favorites = 0
        for user in users:
            others_public = [s for s in public_sets if s.user_id != user.id]
            if not others_public:
                continue
            n_fav = random.randint(3, min(12, len(others_public)))
            for study_set in random.sample(others_public, n_fav):
                exists = Favorite.query.filter_by(
                    user_id=user.id, study_set_id=study_set.id
                ).first()
                if exists:
                    continue
                db.session.add(Favorite(user_id=user.id, study_set_id=study_set.id))
                created_favorites += 1

        db.session.commit()

        created_sessions = 0
        for user in users:
            own_sets = [s for s in all_sets if s.user_id == user.id and len(s.flashcards) >= 2]
            n_sessions = random.randint(8, 35)
            for _ in range(n_sessions):
                if not own_sets:
                    break
                study_set = random.choice(own_sets)
                n_cards = len(study_set.flashcards)
                mode = random.choice(["quiz", "quiz", "time"])
                if mode == "quiz":
                    total = random.randint(3, min(20, n_cards))
                    score = random.randint(0, total)
                else:
                    total = random.randint(5, min(30, n_cards * 2))
                    score = random.randint(int(total * 0.3), total)
                accuracy = score / total if total else 0.0
                days_ago = random.randint(0, 60)
                finished = datetime.now(timezone.utc) - timedelta(
                    days=days_ago,
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
                db.session.add(StudySession(
                    user_id=user.id,
                    study_set_id=study_set.id,
                    mode=mode,
                    score=score,
                    total=total,
                    accuracy=accuracy,
                    finished_at=finished,
                ))
                created_sessions += 1

        db.session.commit()

        total_users = User.query.count()
        total_sets = StudySet.query.count()
        total_cards = Flashcard.query.count()
        total_tags = Tag.query.count()
        total_favs = Favorite.query.count()
        total_sessions = StudySession.query.count()

        print(f"→ Created {created_users} new users, {created_sets} study sets.")
        print(f"→ Also added {created_favorites} favorites, {created_sessions} study sessions.")
        print(
            f"\nDatabase totals: {total_users} users, {total_sets} sets, "
            f"{total_cards} flashcards, {total_tags} tags, "
            f"{total_favs} favorites, {total_sessions} sessions."
        )
        print("\nDemo logins (password is <username>1234 for generated accounts):")
        for spec in CORE_USERS:
            print(f"  {spec['username']:<10}/ {spec['password']}")
        print("  … plus ~47 more student accounts (same password pattern).")


if __name__ == "__main__":
    seed()
