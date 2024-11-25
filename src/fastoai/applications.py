from pathlib import Path

import fsspec
import yaml
from fastapi import FastAPI

from . import __version__
from .settings import settings


class FastOAI(FastAPI):
    def __init__(self, *, title="FastOAI", version=__version__, **kwargs):
        super().__init__(title=title, version=version, **kwargs)

    def openapi(self):
        with fsspec.open(
            "filecache::github://openai:openai-openapi@master/openapi.yaml",
            filecache={"cache_storage": str(Path(__file__).parent)},
        ) as f:
            schema = yaml.load(f, Loader=yaml.SafeLoader)
        schema["servers"] = [{"url": str(settings.base_url)}]
        self.openapi_schema = schema
        return super().openapi()
