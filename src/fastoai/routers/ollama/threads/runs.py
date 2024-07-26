from typing import cast

from fastapi import Depends, HTTPException
from ollama import AsyncClient
from ollama._types import Message as OllamaMessage
from openai.types.beta.thread import Thread as OpenAIThread
from openai.types.beta.thread_create_and_run_params import Thread as ThreadParams
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.image_url_content_block import ImageURLContentBlock
from openai.types.beta.threads.message import Attachment
from openai.types.beta.threads.message import Message as OpenAIMessage
from openai.types.beta.threads.message_content import MessageContent
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock

from ....models.assistant import Assistant
from ....models.message import Message
from ....models.thread import Thread
from ....models.user import User, get_current_active_user
from ....requests import ThreadCreateAndRunParams
from ....routing import OAIRouter
from ....settings import Settings, get_settings
from .._backend import get_ollama

router = OAIRouter(tags=["Runs"])


@router.post("/threads/runs")
async def create_thread_and_run(
    params: ThreadCreateAndRunParams,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
    ollama: AsyncClient = Depends(get_ollama),
):
    assistant = settings.session.get(Assistant, params.assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    thread_params = cast(ThreadParams, params.thread)
    messages = thread_params.pop("messages")
    thread = Thread(data=OpenAIThread(id="dummy", created_at=0, **params.thread))
    settings.session.add(thread)
    settings.session.commit()
    settings.session.refresh(thread)
    openai_messages: list[OpenAIMessage] = []
    for data in messages:
        role = data["role"]
        content: list[MessageContent] = [
            TextContentBlock(text=Text(value=block, annotations=[]), type="text")
            if isinstance(block, str)
            else TextContentBlock(
                text=Text(value=block["text"], annotations=[]), type="text"
            )
            if block["type"] == "text"
            else ImageURLContentBlock.model_validate(block)
            if block["type"] == "image_url"
            else ImageFileContentBlock.model_validate(block)
            for block in data["content"]
        ]
        openai_message = OpenAIMessage(
            id="dummy",
            created_at=0,
            thread_id=thread.id,
            object="thread.message",
            status="completed",
            role=role,
            content=content,
        )
        if data.get("attachments"):
            openai_message.attachments = [
                Attachment.model_validate(attachment)
                for attachment in (data.get("attachments") or [])
            ] or None
        message = Message(
            thread=thread,
            data=openai_message,
        )
        settings.session.add(message)
        settings.session.commit()
        settings.session.refresh(message)
        openai_messages.append(message.data)
    settings.session.commit()
    settings.session.refresh(thread)
    ollama_messages: list[OllamaMessage] = []
    if assistant.data.instructions is not None:
        ollama_messages.append(
            {"role": "system", "content": assistant.data.instructions}
        )
    if params.instructions is not None:
        ollama_messages.append({"role": "system", "content": params.instructions})
    for openai_message in openai_messages:
        current_message: OllamaMessage = {"role": openai_message.role, "content": ""}
        for block in openai_message.content:
            if isinstance(block, TextContentBlock):
                current_message["content"] += block.text.value
                # ollama_messages.append({"role": openai_message.role, "content": block.text.value})
            else:
                ...
        ollama_messages.append(current_message)
        ...
    await ollama.chat(
        messages=ollama_messages,
        model=assistant.data.model,
        stream=params.stream,
    )
