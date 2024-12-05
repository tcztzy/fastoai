from asyncio import timeout
from datetime import datetime
from functools import wraps
from typing import cast

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openai.types.beta.assistant_stream_event import (
    AssistantStreamEvent,
    ErrorEvent,
    ThreadMessageCreated,
    ThreadMessageDelta,
    ThreadMessageInProgress,
    ThreadRunCompleted,
    ThreadRunCreated,
    ThreadRunExpired,
    ThreadRunFailed,
    ThreadRunInProgress,
    ThreadRunQueued,
    ThreadRunStepCreated,
    ThreadRunStepInProgress,
)
from openai.types.beta.threads.run import LastError
from openai.types.beta.threads.run_create_params import (
    RunCreateParams,
    RunCreateParamsStreaming,
)
from openai.types.beta.threads.runs.message_creation_step_details import (
    MessageCreation,
    MessageCreationStepDetails,
)
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.shared import ErrorObject
from pydantic import RootModel

from ...dependencies import OpenAIDependency, SessionDependency
from ...models import (
    Assistant,
    Message,
    Run,
    RunStep,
    Thread,
)


def _(event: AssistantStreamEvent):
    return f"event: {event.event}\ndata: {event.data.model_dump_json()}\n"


def run_decorator(run_model: Run, session: SessionDependency):
    def event_decorator(generator_func):
        @wraps(generator_func)
        async def wrapper(*args, **kwargs):
            yield _(
                ThreadRunCreated(
                    data=await run_model.to_openai_model(),
                    event="thread.run.created",
                )
            )
            try:
                async with timeout(
                    None
                    if run_model.expires_at is None
                    else (run_model.expires_at - datetime.now()).total_seconds()
                ):
                    async for value in generator_func(*args, **kwargs):
                        yield value

                    run_model.status = "completed"
                    session.add(run_model)
                    await session.commit()
                    yield _(
                        ThreadRunCompleted(
                            data=await run_model.to_openai_model(),
                            event="thread.run.completed",
                        )
                    )
                yield "event: done\ndata: [DONE]\n"
            except TimeoutError:
                run_model.status = "expired"
                session.add(run_model)
                await session.commit()
                yield _(
                    ThreadRunExpired(
                        data=await run_model.to_openai_model(),
                        event="thread.run.expired",
                    )
                )
                yield _(
                    ErrorEvent(
                        data=ErrorObject(message="Run expired", type="TimeoutError"),
                        event="error",
                    )
                )
            except Exception as e:
                run_model.status = "failed"
                run_model.last_error = LastError(code="server_error", message=str(e))
                session.add(run_model)
                await session.commit()
                yield _(
                    ThreadRunFailed(
                        data=await run_model.to_openai_model(),
                        event="thread.run.failed",
                    )
                )

        return wrapper

    return event_decorator


router = APIRouter()


@router.post("/threads/{thread_id}/runs")
async def create_run(
    thread_id: str,
    params: RootModel[RunCreateParams],
    session: SessionDependency,
    client: OpenAIDependency,
):
    if not params.root.get("stream", False):
        raise NotImplementedError("Non-streaming is not yet supported")
    run_params = cast(RunCreateParamsStreaming, params.model_dump())
    assistant = await session.get_one(Assistant, run_params["assistant_id"])
    thread = await session.get_one(Thread, thread_id)
    run = Run(  # type: ignore
        assistant=assistant,
        thread=thread,
        status="queued",
        model=run_params.get("model") or assistant.model,
        instructions=run_params.get("instructions") or assistant.instructions or "",
        parallel_tool_calls=run_params.get("parallel_tool_calls", True),
        tools=run_params.get("tools") or assistant.tools,
    )
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": run.instructions},
        *[m.model_dump() for m in thread.messages],  # type: ignore
    ]

    async def message_creation_step():
        message = Message(  # type: ignore
            thread=thread,
            assistant=assistant,
            run=run,
            content=[],
            role="assistant",
            status="in_progress",
        )
        session.add(message)
        step = RunStep(  # type: ignore
            run=run,
            thread=thread,
            assistant=assistant,
            status="in_progress",
            type="message_creation",
            step_details=MessageCreationStepDetails(
                message_creation=MessageCreation(message_id=message.id),
                type="message_creation",
            ),
        )
        yield _(
            ThreadRunStepCreated(
                data=await step.to_openai_model(),
                event="thread.run.step.created",
            )
        )
        session.add(step)
        await session.commit()
        await session.refresh(step)
        yield _(
            ThreadRunStepInProgress(
                data=await step.to_openai_model(),
                event="thread.run.step.in_progress",
            )
        )
        yield _(
            ThreadMessageCreated(
                data=await message.to_openai_model(),
                event="thread.message.created",
            )
        )
        await session.commit()
        await session.refresh(message)
        yield _(
            ThreadMessageInProgress(
                data=await message.to_openai_model(), event="thread.message.in_progress"
            )
        )
        async for part in await client.chat.completions.create(
            model=assistant.model,
            messages=messages,
            stream=True,
        ):
            yield _(
                ThreadMessageDelta.model_validate(
                    dict(
                        event="thread.message.delta",
                        data=dict(
                            id=message.id,
                            delta=dict(
                                content=[
                                    dict(
                                        index=0,
                                        type="text",
                                        text=dict(
                                            value=part.choices[0].delta.content,
                                            annotations=[],
                                        ),
                                    )
                                ],
                                role="assistant",
                            ),
                            object="thread.message.delta",
                        ),
                    )
                )
            )

    @run_decorator(run, session)
    async def xrun():
        session.add(run)
        await session.commit()
        await session.refresh(run)
        yield _(
            ThreadRunQueued(
                event="thread.run.queued",
                data=await run.to_openai_model(),
            )
        )

        yield _(
            ThreadRunInProgress(
                event="thread.run.in_progress",
                data=await run.to_openai_model(),
            )
        )
        async for message in message_creation_step():
            yield message

    return StreamingResponse(xrun())
