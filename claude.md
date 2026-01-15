# ADHD Kanban - Project Documentation

## Project Overview

ADHD Kanban is a full-stack task management application designed specifically to help users with ADHD organize their work using a Kanban board interface. The project consists of a Django REST API backend and a Tauri desktop application frontend.

## Architecture

```
adhd_kanban/
├── backend/                 # Django REST API
│   ├── config/              # Django project settings
│   ├── kanban/              # Main Django app (models, views, API)
│   └── static/              # Static files
│
└── frontend/                # Tauri Desktop App
    ├── src/                 # HTML, CSS, JavaScript
    ├── src-tauri/           # Rust Tauri wrapper
    └── tests/               # Frontend tests
```

### Backend (Django REST API)
- **Framework**: Django 5.2+ with Django REST Framework
- **Database**: PostgreSQL 16
- **Authentication**: Token-based (DRF TokenAuthentication)
- **Deployment**: Railway (production), Docker (local development)

### Frontend (Tauri Desktop App)
- **Framework**: Tauri 2.0 (Rust + WebView)
- **UI**: Vanilla JavaScript, HTML5, CSS3
- **Testing**: Vitest (unit), Playwright (E2E)

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | Django 5.2+, Django REST Framework 3.15+ |
| Database | PostgreSQL 16 |
| API Docs | drf-spectacular (OpenAPI/Swagger) |
| Auth | DRF TokenAuthentication |
| Testing | pytest, pytest-django, factory-boy |
| Server | Gunicorn |
| Static Files | WhiteNoise |
| CORS | django-cors-headers |

### Frontend
| Component | Technology |
|-----------|------------|
| Desktop Framework | Tauri 2.0 |
| Language | Vanilla JavaScript (ES Modules) |
| Styling | Custom CSS (no framework) |
| Unit Testing | Vitest 2.1.0 |
| E2E Testing | Playwright 1.48.0 |
| Build | Rust/Cargo (Tauri) |

## Directory Structure

```
adhd_kanban/
├── backend/                         # Django REST API
│   ├── config/                      # Django project configuration
│   │   ├── settings.py              # Main settings
│   │   ├── urls.py                  # Root URL routing
│   │   ├── wsgi.py                  # WSGI entry point
│   │   └── asgi.py                  # ASGI entry point
│   │
│   ├── kanban/                      # Main Django application
│   │   ├── api/                     # REST API implementation
│   │   │   ├── views.py             # API endpoints
│   │   │   ├── serializers.py       # Data serialization
│   │   │   ├── urls.py              # API URL routing
│   │   │   └── exceptions.py        # Custom error handling
│   │   ├── models.py                # Database models (Column, Task)
│   │   ├── migrations/              # Database migrations
│   │   ├── tests/                   # Backend tests
│   │   │   ├── test_api.py          # API endpoint tests
│   │   │   ├── test_contracts.py    # Contract tests
│   │   │   ├── test_models.py       # Model tests
│   │   │   └── factories.py         # Test data factories
│   │   ├── admin.py                 # Django admin config
│   │   └── templates/               # HTML templates (legacy views)
│   │
│   ├── static/                      # Django static assets
│   ├── docker-compose.yml           # PostgreSQL container
│   ├── requirements.txt             # Python dependencies
│   ├── Procfile                     # Deployment config
│   ├── pytest.ini                   # Pytest configuration
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── manage.py                    # Django CLI
│   └── .env.example                 # Environment template
│
├── frontend/                        # Tauri desktop application
│   ├── src/                         # Frontend source files
│   │   ├── index.html               # Login/registration page
│   │   ├── board.html               # Kanban board page
│   │   ├── js/
│   │   │   ├── api.js               # API client
│   │   │   ├── auth.js              # Auth page logic
│   │   │   └── board.js             # Board logic & drag-drop
│   │   └── css/
│   │       └── style.css            # Application styles
│   ├── src-tauri/                   # Tauri Rust backend
│   │   ├── src/
│   │   │   ├── main.rs              # Entry point
│   │   │   └── lib.rs               # Command handlers
│   │   ├── Cargo.toml               # Rust dependencies
│   │   └── tauri.conf.json          # Tauri configuration
│   ├── tests/                       # Frontend tests
│   │   ├── unit/                    # Vitest unit tests
│   │   ├── e2e/                     # Playwright E2E tests
│   │   ├── mocks/                   # API mocks
│   │   └── setup.js                 # Test setup
│   ├── package.json                 # Node.js dependencies
│   ├── vitest.config.js             # Unit test config
│   └── playwright.config.js         # E2E test config
│
└── railway.toml                     # Railway deployment config
```

## Data Models

### Column
- `user` (FK to User) - Owner (user-scoped)
- `name` (CharField, max 100) - Column title
- `order` (IntegerField) - Display order

### Task
- `user` (FK to User) - Owner (user-scoped)
- `title` (CharField, max 200) - Task title
- `description` (TextField, optional) - Task details
- `column` (FK to Column) - Parent column
- `order` (IntegerField) - Display order
- `created_at`, `updated_at` (DateTimeField) - Timestamps

## API Endpoints

Base URL: `/api/v1/`

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register/` | Create user + default columns |
| POST | `/auth/login/` | Get auth token |
| POST | `/auth/logout/` | Invalidate token |
| GET | `/auth/me/` | Current user info |

### Board
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/board/` | Complete board state |

### Columns
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/columns/` | List user's columns |
| POST | `/columns/` | Create column |
| GET | `/columns/{id}/` | Get column |
| PATCH | `/columns/{id}/` | Update column |
| DELETE | `/columns/{id}/` | Delete column |
| POST | `/reorder-columns/` | Update column order |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/` | List tasks (supports `?column=id`) |
| POST | `/tasks/` | Create task |
| GET | `/tasks/{id}/` | Get task |
| PATCH | `/tasks/{id}/` | Update task |
| DELETE | `/tasks/{id}/` | Delete task |
| POST | `/tasks/{id}/move/` | Move to different column |
| POST | `/reorder-tasks/` | Update task order |

### Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Health check (no auth) |
| GET | `/api/schema/` | OpenAPI schema |
| GET | `/api/docs/` | Swagger UI |

## Development Setup

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd adhd_kanban/backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start PostgreSQL (Docker)**
   ```bash
   docker-compose up -d
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Install Rust/Cargo** (if not installed)
   - Visit https://rustup.rs/

3. **Start Tauri development server**
   ```bash
   npm run tauri dev
   ```

### API Configuration

The frontend connects to the backend API. Update the base URL in `frontend/src/js/api.js`:

```javascript
// For local development
const API_BASE = 'http://localhost:8000/api/v1';

// For production (Railway)
const API_BASE = 'https://adhdkanban-production.up.railway.app/api/v1';
```

## Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=kanban

# Run specific test file
pytest kanban/tests/test_api.py
```

### Frontend Unit Tests
```bash
cd frontend

# Run tests
npm run test

# Run once
npm run test:unit

# With coverage
npm run test:coverage
```

### Frontend E2E Tests
```bash
cd frontend

# Run E2E tests
npm run test:e2e

# Run with visible browser
npm run test:e2e:headed

# Run with Playwright UI
npm run test:e2e:ui
```

## Deployment

### Backend (Railway)
- Configured via `railway.toml` and `Procfile`
- Automatic migrations on deploy
- Static files served via WhiteNoise
- Production URL: `https://adhdkanban-production.up.railway.app`

### Frontend (Tauri)
- Build desktop app:
  ```bash
  cd frontend
  npm run tauri build
  ```
- Outputs platform-specific installers (Windows, macOS, Linux)

## Environment Variables

### Backend (.env)
```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:pass@host:5432/dbname
CORS_ALLOWED_ORIGINS=http://localhost:1420
DJANGO_LOG_LEVEL=INFO
```

### Local Database (docker-compose.yml)
```
DB_NAME=adhd_kanban
DB_USER=kanban_user
DB_PASSWORD=kanban_dev_password
DB_HOST=localhost
DB_PORT=5432
```

## Key Features

### ADHD-Friendly Design
- Maximum 12 columns (prevents overwhelm)
- Clear visual hierarchy
- Minimal distractions
- Drag-and-drop for easy reorganization

### User Features
- Token-based authentication
- User-scoped data (complete isolation)
- Default columns on registration (Backlog, Next, Today, In Progress, Done)
- Task creation with title and description
- Column/task reordering via drag-and-drop
- Inline column renaming (double-click)

### Technical Features
- RESTful API with OpenAPI documentation
- Comprehensive test coverage (backend + frontend)
- Cross-platform desktop app (Tauri)
- Secure token authentication
- CORS support for development

## Code Conventions

### Backend (Python/Django)
- Follow PEP 8
- Use Django REST Framework conventions
- User-scoped querysets on all endpoints
- Factory-based test data generation

### Frontend (JavaScript)
- ES Modules
- Vanilla JS (no framework dependencies)
- DOM manipulation via standard APIs
- API client pattern for all HTTP requests

### Git Workflow
- Main branch for production
- Feature branches for development
- Meaningful commit messages

## Common Tasks

### Add a new API endpoint
1. Define serializer in `backend/kanban/api/serializers.py`
2. Create view in `backend/kanban/api/views.py`
3. Add URL pattern in `backend/kanban/api/urls.py`
4. Write tests in `backend/kanban/tests/test_api.py`

### Add frontend functionality
1. Update API client in `frontend/src/js/api.js`
2. Add UI logic in appropriate JS file
3. Update styles in `frontend/src/css/style.css`
4. Write unit tests in `frontend/tests/unit/`

### Run local development
```bash
# Terminal 1: Backend
cd backend
docker-compose up -d
python manage.py runserver

# Terminal 2: Frontend
cd frontend
npm run tauri dev
```
