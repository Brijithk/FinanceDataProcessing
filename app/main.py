from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import auth, dashboard, records, users
from app.bootstrap import ensure_bootstrap_admin
from app.config import settings
from app.database import Base, engine
from app.models import FinancialRecord, User  # noqa: F401 — register metadata before create_all


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_bootstrap_admin()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(records.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
