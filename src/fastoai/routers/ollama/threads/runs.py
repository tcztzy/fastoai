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
from openai.types.beta.threads.run import Run as OpenAIRun
from openai.types.beta.threads.runs.message_creation_step_details import (
    MessageCreation,
    MessageCreationStepDetails,
)
from openai.types.beta.threads.runs.run_step import RunStep as OpenAIRunStep
from openai.types.beta.threads.text_content_block import TextContentBlock
from pydantic import BaseModel

from ....models.assistant import Assistant
from ....models.message import Message
from ....models.run import Run
from ....models.step import RunStep
from ....models.thread import Thread
from ....models.user import User, get_current_active_user
from ....requests import RunCreateParams
from ....routing import OAIRouter
from ....settings import Settings, get_settings, settings
from .._backend import get_ollama


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
            yield str(
                EventData(event=f"{run_model.data.object}.created", data=run_model.data)
            )
            try:
                async with timeout(
                    None
                    if run_model.data.expires_at is None
                    else run_model.data.expires_at - datetime.now().timestamp()
                ):
                    async for value in generator_func(*args, **kwargs):
                        yield value
                    else:
                        run_model.status = "completed"
                        settings.session.add(run_model)
                        settings.session.commit()
                        yield str(
                            EventData(
                                event=f"{run_model.data.object}.completed",
                                data=run_model.data,
                            )
                        )
            except TimeoutError:
                run_model.status = "expired"
                settings.session.add(run_model)
                settings.session.commit()
                yield str(
                    EventData(
                        event=f"{run_model.data.object}.expired", data=run_model.data
                    )
                )
            except Exception as e:
                print(e)
                run_model.status = "failed"
                run_model.data.last_error = LastError(
                    code="server_error", message=str(e)
                )
                settings.session.add(run_model)
                settings.session.commit()
                yield str(
                    EventData(
                        event=f"{run_model.data.object}.failed", data=run_model.data
                    )
                )
            yield "event: done\ndata: [DONE]\n"

        return wrapper

    return event_decorator


router = OAIRouter(tags=["Runs"])


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
    params: RunCreateParams,  # type: ignore
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
    ollama: AsyncClient = Depends(get_ollama),
):
    if not params.stream:  # type: ignore[attr-defined]
        raise NotImplementedError("Non-streaming is not yet supported")
    assistant = settings.session.get(Assistant, params.assistant_id)  # type: ignore[attr-defined]
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    thread = settings.session.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    openai_run_args = {k: v for k, v in params.model_dump().items() if v}  # type: ignore[attr-defined]
    if "instructions" not in openai_run_args:
        openai_run_args["instructions"] = ""
    if "parallel_tool_calls" not in openai_run_args:
        openai_run_args["parallel_tool_calls"] = True
    if "tools" not in openai_run_args:
        openai_run_args["tools"] = []
    run = Run(
        assistant_id=assistant.id,
        thread_id=thread.id,
        data=OpenAIRun(
            id="dummy",
            created_at=0,
            object="thread.run",
            thread_id=thread.id,
            status="queued",
            model=assistant.data.model,
            **openai_run_args,
        ),
    )
    messages: list[OllamaMessage] = []
    instructions = run.data.instructions or assistant.data.instructions
    if instructions:
        messages.append({"role": "system", "content": instructions})
    messages.extend(
        [
            from_openai_message_to_ollama_message(message.data)
            for message in thread.messages
        ]
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
        yield str(EventData(event=f"{step.data.object}.created", data=step.data))
        settings.session.add(step)
        settings.session.commit()
        settings.session.refresh(step)
        yield str(EventData(event=f"{step.data.object}.in_progress", data=step.data))
        yield str(EventData(event=f"{message.data.object}.created", data=message.data))
        settings.session.add(message)
        settings.session.commit()
        settings.session.refresh(message)
        yield "event: thread.message.in_progress\n"
        yield f"data: {message.data.model_dump_json()}\n\n"
        async for part in await ollama.chat(
            model=assistant.data.model,
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
        yield str(EventData(event=f"{run.data.object}.queued", data=run.data))

        yield str(EventData(event=f"{run.data.object}.in_progress", data=run.data))
        async for message in message_creation_step():
            yield message

    return StreamingResponse(xrun())
