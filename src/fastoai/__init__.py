import importlib.metadata
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.0"

from .routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="FastOAI", version=__version__, lifespan=lifespan)


@app.exception_handler(NoResultFound)
async def no_result_found_exception_handler(_, exc: NoResultFound):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


app.include_router(router)
