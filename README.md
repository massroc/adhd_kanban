# ADHD Kanban Organizer

A task management application designed for ADHD-friendly workflows, built with Django REST Framework backend and Tauri desktop frontend.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

## Local Development Setup

### 1. Clone and Setup Environment

```bash
git clone https://github.com/massroc/adhd_kanban.git
cd adhd_kanban

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start PostgreSQL with Docker

```bash
# Start the database
docker-compose up -d

# Verify it's running
docker ps
```

The database will be available at `localhost:5432` with:
- Database: `kanban`
- User: `kanban_user`
- Password: `kanban_dev_password`

### 3. Configure Environment

Copy the example environment file (or use the provided `.env`):

```bash
cp .env.example .env
```

The default `.env` is configured for Docker PostgreSQL. Edit if needed.

### 4. Run Migrations

```bash
python manage.py migrate
```

Note: The default columns migration (0002) will not create columns automatically anymore. Columns are created per-user when they register.

### 5. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

API available at `http://localhost:8000/api/v1/`

## API Authentication

The API uses token-based authentication. All endpoints except `/auth/*` and `/health/` require authentication.

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123", "password_confirm": "mypassword123"}'
```

Response includes a token and creates default columns (Backlog, Next, Today, In Progress, Done).

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'
```

### Using the Token

Include the token in the Authorization header:

```bash
curl http://localhost:8000/api/v1/board/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/login/` - Login, get token
- `POST /api/v1/auth/logout/` - Logout, invalidate token
- `GET /api/v1/auth/me/` - Get current user info

### Columns
- `GET /api/v1/columns/` - List user's columns
- `POST /api/v1/columns/` - Create column
- `GET /api/v1/columns/{id}/` - Get column
- `PATCH /api/v1/columns/{id}/` - Update column
- `DELETE /api/v1/columns/{id}/` - Delete column

### Tasks
- `GET /api/v1/tasks/` - List user's tasks
- `POST /api/v1/tasks/` - Create task
- `GET /api/v1/tasks/{id}/` - Get task
- `PATCH /api/v1/tasks/{id}/` - Update task
- `DELETE /api/v1/tasks/{id}/` - Delete task
- `POST /api/v1/tasks/{id}/move/` - Move task to different column

### Board
- `GET /api/v1/board/` - Get complete board state (all columns with tasks)

### Reordering
- `POST /api/v1/reorder-columns/` - Reorder columns
- `POST /api/v1/reorder-tasks/` - Reorder tasks

### Health
- `GET /api/v1/health/` - Health check (no auth required)

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kanban

# Run specific test file
pytest kanban/tests/test_api.py
```

## Stopping the Database

```bash
docker-compose down

# To also remove the data volume:
docker-compose down -v
```

## Project Structure

```
adhd_kanban/
├── config/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── kanban/              # Main application
│   ├── api/             # REST API
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── migrations/
│   ├── tests/
│   │   ├── factories.py
│   │   ├── test_api.py
│   │   ├── test_contracts.py
│   │   └── test_models.py
│   ├── models.py
│   └── views.py         # Legacy web views
├── docker-compose.yml   # PostgreSQL for local dev
├── requirements.txt
├── .env                 # Local environment config
└── .env.example         # Template for environment
```

## Deployment

See deployment documentation (coming soon) for Railway/Render setup.
