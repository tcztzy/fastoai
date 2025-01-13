from typing import Literal, Type, overload

from loguru import logger
from openai import AsyncOpenAI as _AsyncOpenAI
from openai._base_client import _AsyncStreamT
from openai._models import FinalRequestOptions
from openai._types import ResponseT
from openai.types.model import Model
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_random_exponential


class Endpoint(BaseModel):
    base_url: str
    api_key: str
    models: list[Model] = Field(default_factory=list)
    count: int = 0
    failure_count: int = 0


class AsyncOpenAI(_AsyncOpenAI):
    """Load-balanced OpenAI client."""

    failure_threshold: int

    def __init__(
        self,
        *,
        endpoints: dict[tuple[str, str], list[Model]],
        failure_threshold: int = 10,
        **kwargs,
    ):
        self.endpoints = [
            Endpoint(base_url=base_url, api_key=api_key, models=models)
            for (base_url, api_key), models in endpoints.items()
        ]
        self.failure_threshold = failure_threshold
        super().__init__(**kwargs)

    @overload
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: Literal[False] = False,
        remaining_retries: int | None = None,
    ) -> ResponseT: ...

    @overload
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: Literal[True],
        stream_cls: type[_AsyncStreamT],
        remaining_retries: int | None = None,
    ) -> _AsyncStreamT: ...

    @overload
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: bool,
        stream_cls: type[_AsyncStreamT] | None = None,
        remaining_retries: int | None = None,
    ) -> ResponseT | _AsyncStreamT: ...

    @retry(wait=wait_random_exponential(max=10), stop=stop_after_attempt(3))
    async def request(
        self,
        cast_to: Type[ResponseT],
        options: FinalRequestOptions,
        *,
        stream: bool = False,
        stream_cls: type[_AsyncStreamT] | None = None,
        remaining_retries: int | None = None,
    ) -> ResponseT | _AsyncStreamT:
        exceptions = []
        model = (
            options.json_data.get("model")
            if isinstance(options.json_data, dict)
            else None
        )
        endpoints = [
            p
            for p in sorted(self.endpoints, key=lambda x: x.failure_count)
            if p.failure_count < self.failure_threshold
            if model is None or any(m.id == model for m in p.models)
        ]

        for endpoint in endpoints:
            try:
                endpoint.count += 1
                return (
                    await super()
                    .with_options(api_key=endpoint.api_key, base_url=endpoint.base_url)
                    .request(
                        cast_to,
                        options,
                        stream=stream,
                        stream_cls=stream_cls,
                        remaining_retries=remaining_retries,
                    )
                )
            except Exception as exc:
                logger.error(
                    f"Error from endpoint={endpoint.base_url} api_key={endpoint.api_key}: {exc}"
                )
                exceptions.append(exc)
                endpoint.failure_count += 1
        raise exceptions[-1] if exceptions else RuntimeError("No endpoints available")
