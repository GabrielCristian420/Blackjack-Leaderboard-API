# Blackjack Leaderboard API

A production-style FastAPI backend for a Blackjack leaderboard. The project exposes authenticated score submission, leaderboard retrieval, and paginated player history, with validation, rate limiting, logging, tests, and Docker support.

> **Connected Project:** This API serves as the backend for the Blackjack game built in C#: [BlackjackPOO](https://github.com/GabrielCristian420/BlackjackPOO)

## Highlights

- JWT authentication for write operations via `POST /token` and `POST /scores`
- Fixed-window rate limiting on score submission
- Strong request validation with Pydantic
- Paginated history for each player
- Structured request logging with request IDs
- OpenAPI docs with request/response examples and error models
- Alembic migrations for database versioning
- Automated tests with Pytest
- Local SQLite support and PostgreSQL via Docker Compose
- Static demo frontend for quick portfolio presentation

## Tech Stack

- Python 3.14+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PyJWT
- SQLite for local development
- PostgreSQL for containerized deployment
- Uvicorn

## Project Structure

- `main.py` - FastAPI app, routes, middleware, and auth endpoint
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response schemas
- `security.py` - JWT creation and verification helpers
- `database.py` - database session setup
- `alembic/` - migration environment and revisions
- `tests/` - automated API tests
- `demo/index.html` - static demo page

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables. At minimum, set these values:

```env
DATABASE_URL=sqlite:///./leaderboard.db
JWT_SECRET_KEY=change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW_SECONDS=60
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

4. Apply database migrations:

```bash
alembic upgrade head
```

5. Start the API:

```bash
uvicorn main:app --reload
```

## Authentication Flow

The API uses a simple JWT flow designed for demo and portfolio use.

1. Request a token:

```bash
curl -X POST http://127.0.0.1:8000/token ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=GameServer&password=password123"
```

2. Use the returned `access_token` as a Bearer token when calling `POST /scores`.

Accepted demo credentials:

- Username: `GameServer`
- Password: `password123`

Invalid credentials return `401 Unauthorized`.

## API Endpoints

- `POST /token` - returns a JWT access token for the demo client
- `POST /scores` - adds a new score, protected by JWT
- `GET /scores` - returns the top 10 scores
- `GET /player/{name}` - returns paginated score history for one player

### `POST /scores` payload

```json
{
  "player_name": "Maria",
  "score": 250
}
```

### `GET /player/{name}` response

```json
{
  "page": 1,
  "page_size": 50,
  "total": 123,
  "items": [
    {
      "id": 1,
      "player_name": "Maria",
      "score": 250,
      "timestamp": "2026-04-01T10:30:00"
    }
  ]
}
```

## Running Tests

```bash
pytest -q
```

The test suite covers:

- JWT-protected score submission
- Token issuance and invalid login handling
- Validation errors for malformed input
- Player history pagination
- Large-volume pagination behavior

## Docker

Start the full stack with PostgreSQL:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

The container entrypoint runs Alembic migrations before starting Uvicorn.

## Demo Frontend

A lightweight static demo is available in `demo/index.html`.

To preview it locally:

```bash
python -m http.server 3000
```

Then open:

`http://localhost:3000/demo/index.html`

## Notes

- Swagger UI is available at `/docs`.
- ReDoc is available at `/redoc`.
- CORS is preconfigured for `http://localhost:3000` and `http://localhost:5173`.
