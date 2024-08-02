from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute


class MetadataRenameRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def rename_metadata_route_handler(request: Request) -> Response:
            response: Response = await original_route_handler(request)
            response.body = response.body.replace(b'"metadata_"', b'"metadata"')
            response.headers["Content-Length"] = str(len(response.body))
            return response

        return rename_metadata_route_handler
