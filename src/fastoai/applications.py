from fastapi import FastAPI

from . import __version__


class FastOAI(FastAPI):
    def __init__(self, *, title="FastOAI", version=__version__, **kwargs):
        self.openapi_fixed = False
        super().__init__(title=title, version=version, **kwargs)

    def openapi(self):
        if self.openapi_fixed:
            return self.openapi()
        openapi_schema = super().openapi()
        self.openapi_fixed = True
        self.openapi_schema = openapi_schema
        return openapi_schema
