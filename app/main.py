"""
Main FastAPI application for Money Fest
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, batches, transactions, categories, rules


# Create FastAPI application
app = FastAPI(
    title="Money Fest",
    description="Collaborative Bank Transaction Categorizer",
    version="0.1.0"
)


# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(batches.router, prefix="/batches", tags=["batches"])
app.include_router(transactions.router, tags=["transactions"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(rules.router, prefix="/rules", tags=["rules"])


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Startup event to initialize database
@app.on_event("startup")
def startup_event():
    """Initialize database on application startup"""
    init_db()
    print("Database initialized successfully")


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {"status": "ok"}


# Root redirect to login page
@app.get("/")
def root():
    """Redirect root to login page"""
    return RedirectResponse(url="/static/index.html")
