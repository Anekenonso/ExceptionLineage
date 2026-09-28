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

cors_kwargs: dict = {
    "allow_origins": settings.cors_origins_list,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.cors_origin_regex:
    cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex

app.add_middleware(CORSMiddleware, **cors_kwargs)


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.effective_port, reload=True)


