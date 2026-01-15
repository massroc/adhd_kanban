# E2E Tests

End-to-end tests for the ADHD Kanban frontend using Playwright.

## Prerequisites

1. **Backend running** at `http://localhost:8000`
   ```bash
   cd backend
   docker-compose up -d
   python manage.py runserver
   ```

2. **Frontend dependencies** installed
   ```bash
   cd frontend
   npm install
   ```

## Running Tests

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run with browser visible
npm run test:e2e:headed

# Run with Playwright interactive UI
npm run test:e2e:ui
```

## Test User Setup

Tests automatically create a test user on first run via the **global setup**.

The global setup:
1. Attempts to register `e2e_test_user` via the API
2. If user exists, logs in instead
3. Stores the token for test use

You can also manually create a test user:
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "e2e_test_user", "password": "e2e_test_password_123", "password_confirm": "e2e_test_password_123"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_USERNAME` | `e2e_test_user` | Test user username |
| `TEST_PASSWORD` | `e2e_test_password_123` | Test user password |
| `TEST_API_BASE` | `http://localhost:8000/api/v1` | Backend API URL |
| `TEST_FRONTEND_URL` | `http://localhost:1420` | Frontend URL |
| `CI` | - | Set in CI environments |

## Test Files

| File | Description |
|------|-------------|
| `auth.spec.js` | Authentication flows - login, register, logout |
| `board.spec.js` | Board operations - tasks, drag-drop |
| `column.spec.js` | Column CRUD - create, rename, delete |
| `test-utils.js` | Shared utilities and helpers |
| `global-setup.js` | Playwright global setup |

## Writing Tests

### Using Test Utilities

```javascript
import { test, expect } from '@playwright/test';
import { loginUser, TEST_USER } from './test-utils.js';

test('my test', async ({ page }) => {
    // Login helper
    await loginUser(page);

    // Now you're on the board page
    await expect(page.locator('#kanban-board')).toBeVisible();
});
```

### Test Patterns

1. **Always clear localStorage** before auth tests
2. **Use `loginUser` helper** for tests that need authentication
3. **Set appropriate timeouts** for async operations
4. **Handle conditional skips** for environment-dependent tests

## Debugging

```bash
# Run single test file
npx playwright test column.spec.js

# Run single test by name
npx playwright test -g "can create a new column"

# Debug mode (step through)
npx playwright test --debug

# Show browser during test
npm run test:e2e:headed
```

## CI/CD

Tests are configured to run in CI with:
- 2 retries on failure
- No server reuse (starts fresh)
- HTML report generation

The GitHub Actions workflow runs these tests automatically on PRs.
