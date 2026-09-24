from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.investigations.exceptions import InvestigationNotFoundError
from app.investigations.router import router as investigations_router

app = FastAPI(
    title="ExceptionLineage API",
    description="Evidence-backed investigation for enterprise transaction exceptions",
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount investigations API router
app.include_router(
    investigations_router,
    prefix="/api/investigations",
    tags=["investigations"],
)


@app.exception_handler(InvestigationNotFoundError)
async def investigation_not_found_handler(
    request: Request, exc: InvestigationNotFoundError
) -> JSONResponse:
    """Return structured HTTP 404 response when an investigation is not found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
    }

