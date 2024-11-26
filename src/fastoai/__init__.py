import importlib.metadata
from contextlib import asynccontextmanager

from fastapi import FastAPI

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.0"

from .routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="FastOAI", version=__version__, lifespan=lifespan)
app.include_router(router)
