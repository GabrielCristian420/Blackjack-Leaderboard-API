import json
import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models
import schemas
from database import SessionLocal
from security import create_access_token, verify_jwt
from settings import get_settings

settings = get_settings()


logger = logging.getLogger("blackjack_api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(settings.log_level.upper())


class FixedWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        threshold = now - self.window_seconds

        with self.lock:
            history = self.requests[key]
            while history and history[0] < threshold:
                history.popleft()

            if len(history) >= self.max_requests:
                return False

            history.append(now)
            return True


write_rate_limiter = FixedWindowRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

app = FastAPI(title="Blackjack Leaderboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def structured_request_logging(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    client_ip = get_client_ip(request)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            json.dumps(
                {
                    "event": "request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                }
            )
        )
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


# Dependență pentru a obține o sesiune de bază de date
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_write_rate_limit(request: Request):
    if not settings.rate_limit_enabled:
        return

    key = get_client_ip(request)
    allowed = write_rate_limiter.allow(key)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many write requests. "
                f"Limit is {settings.rate_limit_requests} requests per "
                f"{settings.rate_limit_window_seconds} seconds."
            ),
        )


@app.post(
    "/token",
    response_model=schemas.TokenResponse,
    tags=["auth"],
    summary="Get a JWT access token",
    responses={401: {"model": schemas.ErrorResponse, "description": "Invalid credentials"}},
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    if form_data.username != "GameServer" or form_data.password != "password123":
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(
    "/scores",
    response_model=schemas.ScoreResponse,
    tags=["scores"],
    summary="Add a new score",
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Missing or invalid JWT"},
        422: {"model": schemas.ErrorResponse, "description": "Validation error"},
        429: {
            "model": schemas.ErrorResponse,
            "description": "Write rate limit exceeded",
        },
    },
)
def add_score(
    score: schemas.ScoreCreate = Body(
        ...,
        examples=[
            {
                "summary": "Valid score payload",
                "value": {"player_name": "Maria", "score": 250},
            }
        ],
    ),
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(check_write_rate_limit),
    _auth_payload: dict = Depends(verify_jwt),
):
    """Adaugă un scor nou pentru un jucător."""
    db_score = models.Score(player_name=score.player_name, score=score.score)
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score


@app.get(
    "/scores",
    response_model=list[schemas.ScoreResponse],
    tags=["scores"],
    summary="Get top 10 scores",
)
def get_top_scores(db: Session = Depends(get_db)):
    """Afișează top 10 cele mai mari scoruri (Leaderboard)."""
    top_scores = (
        db.query(models.Score).order_by(models.Score.score.desc()).limit(10).all()
    )
    return top_scores


@app.get(
    "/player/{name}",
    response_model=schemas.PlayerScoreHistoryResponse,
    tags=["players"],
    summary="Get paginated score history for one player",
    responses={
        404: {"model": schemas.ErrorResponse, "description": "Player not found"}
    },
)
def get_player_history(
    name: str = Path(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9 _-]+$"),
    page: int = Query(default=1, ge=1, description="1-based page index"),
    page_size: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Number of records per page (max 100)",
    ),
    db: Session = Depends(get_db),
):
    """Afișează istoricul scorurilor pentru un anumit jucător."""
    query = db.query(models.Score).filter(models.Score.player_name == name)
    total = query.count()

    if total == 0:
        raise HTTPException(
            status_code=404, detail="Jucătorul nu a fost găsit sau nu are scoruri."
        )

    player_history = (
        query.order_by(models.Score.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": player_history,
    }
