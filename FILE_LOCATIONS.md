# File Locations

Every file in this download and exactly where it goes in your project.

Your project root is `adhd_kanban/` (the folder containing `manage.py`).

## Complete File List

Copy each file to the path shown. Replace existing files.

```
adhd_kanban/
├── .env                          # NEW - copy to project root
├── .env.example                  # NEW - copy to project root
├── .gitignore                    # REPLACE existing
├── README.md                     # REPLACE existing
├── SETUP_INSTRUCTIONS.md         # NEW - copy to project root (optional, for reference)
├── conftest.py                   # REPLACE existing
├── docker-compose.yml            # NEW - copy to project root
├── manage.py                     # REPLACE existing (unchanged but included)
├── pytest.ini                    # REPLACE existing (unchanged but included)
├── requirements.txt              # REPLACE existing
│
├── config/
│   ├── __init__.py               # REPLACE (unchanged)
│   ├── asgi.py                   # REPLACE (unchanged)
│   ├── settings.py               # REPLACE - major changes
│   ├── urls.py                   # REPLACE (unchanged)
│   └── wsgi.py                   # REPLACE (unchanged)
│
├── kanban/
│   ├── __init__.py               # REPLACE (unchanged)
│   ├── admin.py                  # REPLACE - added user fields
│   ├── apps.py                   # REPLACE (unchanged)
│   ├── models.py                 # REPLACE - added user FK
│   ├── urls.py                   # REPLACE (unchanged)
│   ├── views.py                  # REPLACE - added auth
│   │
│   ├── api/
│   │   ├── __init__.py           # REPLACE (unchanged)
│   │   ├── serializers.py        # REPLACE - major changes
│   │   ├── urls.py               # REPLACE - added auth endpoints
│   │   └── views.py              # REPLACE - major changes
│   │
│   ├── migrations/
│   │   ├── __init__.py           # REPLACE (unchanged)
│   │   ├── 0001_initial.py       # REPLACE (unchanged)
│   │   ├── 0002_default_columns.py   # REPLACE - now a no-op
│   │   ├── 0003_add_user_to_models.py    # NEW
│   │   └── 0004_make_user_non_nullable.py # NEW
│   │
│   ├── templates/
│   │   └── kanban/
│   │       └── board.html        # REPLACE (unchanged)
│   │
│   └── tests/
│       ├── __init__.py           # REPLACE (unchanged)
│       ├── factories.py          # REPLACE - added UserFactory
│       ├── test_api.py           # REPLACE - major changes
│       ├── test_contracts.py     # REPLACE - added auth
│       └── test_models.py        # REPLACE - added user tests
│
└── static/
    └── .gitkeep                  # REPLACE (unchanged)
```

## Files with Major Changes

These are the files with significant code changes (not just unchanged copies):

| File | What Changed |
|------|--------------|
| `config/settings.py` | Loads .env, PostgreSQL config, token auth enabled |
| `kanban/models.py` | Added `user` ForeignKey to Column and Task |
| `kanban/views.py` | Added LoginRequiredMixin, filters by user |
| `kanban/admin.py` | Added user to list displays |
| `kanban/api/views.py` | Auth endpoints, all queries filtered by user |
| `kanban/api/serializers.py` | User validation, auth serializers added |
| `kanban/api/urls.py` | Added /auth/* routes |
| `kanban/migrations/0002_default_columns.py` | Changed to no-op |
| `kanban/migrations/0003_add_user_to_models.py` | NEW migration |
| `kanban/migrations/0004_make_user_non_nullable.py` | NEW migration |
| `kanban/tests/factories.py` | Added UserFactory |
| `kanban/tests/test_api.py` | All tests use auth fixtures |
| `kanban/tests/test_contracts.py` | Added auth schema tests |
| `kanban/tests/test_models.py` | Added user isolation tests |
| `requirements.txt` | Added python-dotenv |
| `conftest.py` | Added auth fixtures |
| `docker-compose.yml` | NEW - PostgreSQL container |
| `.env` | NEW - local environment config |

## New Files (don't exist in your current project)

```
.env
.env.example
docker-compose.yml
SETUP_INSTRUCTIONS.md
kanban/migrations/0003_add_user_to_models.py
kanban/migrations/0004_make_user_non_nullable.py
```

## Setup Commands (after copying files)

```bash
cd adhd_kanban

# Delete old database
rm -f db.sqlite3

# Start PostgreSQL
docker-compose up -d

# Activate virtualenv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests (expect 50+ passing)
pytest

# Start server
python manage.py runserver
```
