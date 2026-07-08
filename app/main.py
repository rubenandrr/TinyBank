"""
Main entrypoint for the Tiny Bank API.
Configures the FastAPI application, handles exceptions globally,
and registers all routing modules.
"""

from fastapi import FastAPI, Request # type: ignore
from fastapi.responses import JSONResponse, RedirectResponse # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore

from app.exceptions import BankException
from app.routers import (
    user_router,
    account_router,
    transaction_router,
    audit_router,
    auth_router,
)

# API initialization
app = FastAPI(
    title="Tiny Bank API",
    description=(
        "Modern banking simulation API. "
        "Manages multi-currency accounts (CHF by default, EUR, USD), transfers "
        "with automatic exchange conversion, banking commission fees, spent limits, "
        "and security audit trails."
    ),
    version="2.0.0",
)

# --- CORS Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Business Logic Exception Handler ---

@app.exception_handler(BankException)
async def bank_exception_handler(request: Request, exc: BankException):
    """
    Automatically intercepts any BankException raised in services or routers
    and returns a formatted JSON response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.message
        }
    )

# --- Default Root Redirection & Configurations ---

@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects root requests to the interactive Swagger documentation.
    """
    return RedirectResponse(url="/docs")

@app.get("/config", tags=["Configuration"])
async def get_config():
    """
    Returns the current banking configurations, including exchange rates
    and transaction margins.
    """
    from app.config import EXCHANGE_RATES, BANK_MARGIN
    return {
        "exchange_rates": EXCHANGE_RATES,
        "bank_margin": BANK_MARGIN
    }

@app.post("/reset", tags=["Configuration"])
async def reset_database():
    """
    Resets and clears the entire in-memory database storage.
    """
    from app.database import reset_db
    reset_db()
    return {"message": "Database reset successful"}

# --- Inclusion of Modular Routers ---

app.include_router(user_router)
app.include_router(account_router)
app.include_router(transaction_router)
app.include_router(audit_router)
app.include_router(auth_router)