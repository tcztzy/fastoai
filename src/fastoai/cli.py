from typing import Annotated
from urllib.parse import urlparse

import typer
import uvicorn

from .settings import settings

app = typer.Typer()


result = urlparse(str(settings.base_url))
DEFAULT_HOST = result.hostname or "127.0.0.1"
DEFAULT_PORT = result.port or 8000


@app.command()
def serve(
    host: Annotated[
        str, typer.Option(help="If not specified, will read from env FASTOAI_BASE_URL")
    ] = DEFAULT_HOST,
    port: Annotated[
        int,
        typer.Option(help="If not specified, will read from env FASTOAI_BASE_URL"),
    ] = DEFAULT_PORT,
    reload: bool = False,
):
    """Serve the FastAPI application."""
    print(settings.generate_models)
    uvicorn.run(
        "fastoai:app",
        host=host,
        port=port,
        reload=reload,
        reload_excludes=["generated/*.py"],
    )
