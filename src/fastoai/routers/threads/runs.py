import json
from asyncio import timeout
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from ollama import AsyncClient
from ollama._types import Message as OllamaMessage
from openai.types.beta.threads.message import Message as OpenAIMessage
from openai.types.beta.threads.run import LastError
from openai.types.beta.threads.runs.message_creation_step_details import (
    MessageCreation,
    MessageCreationStepDetails,
)
from openai.types.beta.threads.runs.run_step import RunStep as OpenAIRunStep
from openai.types.beta.threads.text_content_block import TextContentBlock
from pydantic import BaseModel

from ...models import (
    Assistant,
    Message,
    Run,
    RunStep,
    Thread,
    User,
    get_current_active_user,
)
from ...requests import RunCreateParams
from ...routing import OAIRouter
from ...settings import Settings, get_settings, settings
from .._backend import get_ollama
from .._fix import MetadataRenameRoute


@dataclass
class EventData:
    event: str
    data: BaseModel

    def __str__(self) -> str:
        return f"event: {self.event}\ndata: {self.data.model_dump_json()}\n\n"


def run_decorator(run_model: Run):
    def event_decorator(generator_func):
        @wraps(generator_func)
        async def wrapper(*args, **kwargs):
            yield str(EventData(event=f"{run_model.object}.created", data=run_model))
            try:
                async with timeout(
                    None
                    if run_model.expires_at is None
                    else run_model.expires_at - datetime.now().timestamp()
                ):
                    async for value in generator_func(*args, **kwargs):
                        yield value

                    run_model.status = "completed"
                    settings.session.add(run_model)
                    settings.session.commit()
                    yield str(
                        EventData(
                            event=f"{run_model.object}.completed",
                            data=run_model,
                        )
                    )
            except TimeoutError:
                run_model.status = "expired"
                settings.session.add(run_model)
                settings.session.commit()
                yield str(
                    EventData(event=f"{run_model.object}.expired", data=run_model)
                )
            except Exception as e:
                run_model.status = "failed"
                run_model.last_error = LastError(code="server_error", message=str(e))
                settings.session.add(run_model)
                settings.session.commit()
                yield str(EventData(event=f"{run_model.object}.failed", data=run_model))
            yield "event: done\ndata: [DONE]\n"

        return wrapper

    return event_decorator


router = OAIRouter(tags=["Runs"], route_class=MetadataRenameRoute)


def from_openai_message_to_ollama_message(message: OpenAIMessage) -> OllamaMessage:
    if any(not isinstance(block, TextContentBlock) for block in message.content):
        raise NotImplementedError("Only text content is supported")
    result: OllamaMessage = {
        "role": message.role,
        "content": "".join(
            [
                block.text.value
                for block in message.content
                if isinstance(block, TextContentBlock)
            ]
        ),
    }
    return result


class OllamaMessageDelta(BaseModel):
    class Message(BaseModel):
        role: str
        content: str

    model: str
    created_at: datetime
    message: Message
    done: bool


@router.post("/threads/{thread_id}/runs")
async def create_run(
    thread_id: str,
    params: RunCreateParams,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
    ollama: AsyncClient = Depends(get_ollama),
):
    if not params.stream:
        raise NotImplementedError("Non-streaming is not yet supported")
    assistant = settings.session.get(Assistant, params.assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    thread = settings.session.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    openai_run_args = {k: v for k, v in params.model_dump().items() if v}
    if "instructions" not in openai_run_args:
        openai_run_args["instructions"] = ""
    if "parallel_tool_calls" not in openai_run_args:
        openai_run_args["parallel_tool_calls"] = True
    if "tools" not in openai_run_args:
        openai_run_args["tools"] = []
    run = Run(
        assistant=assistant,
        thread=thread,
        status="queued",
        model=assistant.model,
        **openai_run_args,
    )
    messages: list[OllamaMessage] = []
    instructions = run.instructions or assistant.instructions
    if instructions:
        messages.append({"role": "system", "content": instructions})
    messages.extend(
        [from_openai_message_to_ollama_message(message) for message in thread.messages]
    )

    async def message_creation_step():
        message = Message(
            thread=thread,
            assistant=assistant,
            run=run,
            data=OpenAIMessage(
                id="dummy",
                created_at=0,
                content=[],
                object="thread.message",
                role="assistant",
                status="in_progress",
                thread_id=thread.id,
            ),
        )
        settings.session.add(message)
        step = RunStep(
            run_id=run.id,
            assistant_id=assistant.id,
            thread_id=thread.id,
            data=OpenAIRunStep(
                id="dummy",
                created_at=0,
                object="thread.run.step",
                run_id=run.id,
                thread_id=thread.id,
                assistant_id=assistant.id,
                status="in_progress",
                type="message_creation",
                step_details=MessageCreationStepDetails(
                    message_creation=MessageCreation(message_id=message.id),
                    type="message_creation",
                ),
            ),
        )
        yield str(EventData(event=f"{step.object}.created", data=step))
        settings.session.add(step)
        settings.session.commit()
        settings.session.refresh(step)
        yield str(EventData(event=f"{step.object}.in_progress", data=step))
        yield str(EventData(event=f"{message.object}.created", data=message))
        settings.session.commit()
        settings.session.refresh(message)
        yield "event: thread.message.in_progress\n"
        yield f"data: {message.model_dump_json()}\n\n"
        async for part in await ollama.chat(
            model=assistant.model,
            messages=messages,
            stream=True,
        ):
            yield "event: thread.message.delta\n"
            yield (
                json.dumps(
                    {
                        "id": message.id,
                        "object": "thread.message.delta",
                        "delta": {
                            "content": [
                                {
                                    "index": 0,
                                    "type": "text",
                                    "text": {
                                        "value": part["message"]["content"],
                                        "annotations": [],
                                    },
                                }
                            ]
                        },
                    }
                )
                + "\n\n"
            )
            yield json.dumps(part) + "\n\n"

    @run_decorator(run)
    async def xrun():
        settings.session.add(run)
        settings.session.commit()
        settings.session.refresh(run)
        yield str(EventData(event=f"{run.object}.queued", data=run))

        yield str(EventData(event=f"{run.object}.in_progress", data=run))
        async for message in message_creation_step():
            yield message

    return StreamingResponse(xrun())
