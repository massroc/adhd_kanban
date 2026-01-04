# Setup Instructions

## Files to Copy

Copy all files from this download to your project root (`adhd_kanban/`), replacing existing files.

### File locations (relative to project root):

```
adhd_kanban/
├── .env                                    # NEW - local environment config
├── .env.example                            # NEW - template
├── README.md                               # UPDATED - new setup docs
├── conftest.py                             # UPDATED - shared test fixtures
├── docker-compose.yml                      # NEW - PostgreSQL container
├── config/
│   └── settings.py                         # UPDATED - dotenv, PostgreSQL, token auth
├── kanban/
│   ├── models.py                           # UPDATED - user foreign keys
│   ├── views.py                            # UPDATED - login required
│   ├── api/
│   │   ├── serializers.py                  # UPDATED - user validation, auth serializers
│   │   ├── urls.py                         # UPDATED - auth endpoints
│   │   └── views.py                        # UPDATED - user filtering, auth views
│   ├── migrations/
│   │   ├── 0002_default_columns.py         # UPDATED - now a no-op
│   │   ├── 0003_add_user_to_models.py      # NEW
│   │   └── 0004_make_user_non_nullable.py  # NEW
│   └── tests/
│       ├── factories.py                    # UPDATED - user factory
│       ├── test_api.py                     # UPDATED - auth tests
│       ├── test_contracts.py               # UPDATED - auth tests
│       └── test_models.py                  # UPDATED - user tests
```

## Step-by-Step Setup

### 1. Install Docker Desktop (if not already installed)

Download from: https://www.docker.com/products/docker-desktop/

After installation, make sure Docker is running (check system tray icon).

### 2. Navigate to your project

```bash
cd /path/to/adhd_kanban
```

### 3. Copy downloaded files

Copy all files from this download into your project, replacing existing files.

### 4. Delete old SQLite database

```bash
rm -f db.sqlite3
```

Or in PowerShell if rm doesn't work:
```powershell
Remove-Item db.sqlite3 -ErrorAction SilentlyContinue
```

### 5. Start PostgreSQL

```bash
docker-compose up -d
```

Verify it's running:
```bash
docker ps
```

You should see `kanban_postgres` in the list.

### 6. Activate your virtual environment

```bash
# Linux/Mac
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Git Bash)
source venv/Scripts/activate
```

### 7. Install new dependency (python-dotenv)

```bash
pip install python-dotenv
```

Or reinstall all:
```bash
pip install -r requirements.txt
```

### 8. Run migrations

```bash
python manage.py migrate
```

### 9. Create a superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 10. Run tests

```bash
pytest
```

Expected: 50+ tests passing.

### 11. Start the development server

```bash
python manage.py runserver
```

### 12. Test the app

**Web interface (requires login):**
- Go to http://localhost:8000/
- You'll be redirected to /admin/login/
- Login with your superuser credentials
- You'll see the board with default columns created for you

**API (token auth):**
```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123", "password_confirm": "testpass123"}'

# Response includes token, save it
# {"user": {"id": 2, "username": "testuser"}, "token": "abc123..."}

# Use token for API calls
curl http://localhost:8000/api/v1/board/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

## Stopping PostgreSQL

```bash
docker-compose down
```

To also delete all data:
```bash
docker-compose down -v
```

## Troubleshooting

**"connection refused" errors:**
- Make sure Docker Desktop is running
- Run `docker-compose up -d` again
- Check with `docker ps` that the container is running

**Migration errors about existing tables:**
- Delete db.sqlite3 if it exists
- Make sure you're connected to PostgreSQL (check .env settings)

**Import errors for dotenv:**
- Run `pip install python-dotenv`

**Tests failing with authentication errors:**
- Make sure you copied all test files including conftest.py
