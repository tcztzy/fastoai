import importlib.metadata
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import fsspec
import yaml
from fastapi import FastAPI

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.0"

from .routers import router
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await settings.session.close()


app = FastAPI(title="FastOAI", version=__version__, lifespan=lifespan)
app.include_router(router)
with fsspec.open(
    "filecache::github://openai:openai-openapi@master/openapi.yaml",
    mode="r",
    filecache={"cache_storage": str(Path(__file__).parent)},
) as f:
    text = cast(str, f.read())
    text = text.replace("https://api.openai.com/v1/", str(settings.base_url))
    schema = yaml.safe_load(text)
original_schema = app.openapi()
schema["info"] = original_schema["info"]
del schema["servers"]
app.openapi_schema = schema
