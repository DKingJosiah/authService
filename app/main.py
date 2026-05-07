from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from . import models
from .database import engine
from .routers import auth, password, sessions
from fastapi.middleware.cors import CORSMiddleware 
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .utils import limiter

app = FastAPI(title="Auth Microservice", description="FastAPI microservice for user authentication")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware 
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)


# ── Global Exception Handlers ────────────────────────────────────
# All errors now return: { "success": false, "message": "...", "data": null }

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles HTTPException (e.g. 400, 401, 404, etc.)"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors (e.g. missing fields, wrong types, password mismatch)."""
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "data": errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catches any unhandled exception. In dev, we show the message."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"An unexpected error occurred: {str(exc)}",
            "data": None,
        },
    )


# ── Routers ───────────────────────────────────────────────────────

from .routers import auth, password, sessions, application

app.include_router(application.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(password.router, prefix="/password", tags=["password-management"])
app.include_router(sessions.router, prefix="/sessions", tags=["session-management"])

@app.get("/health")
def health_check():
    return {"success": True, "message": "Service is healthy", "data": {"service": "auth"}}
    