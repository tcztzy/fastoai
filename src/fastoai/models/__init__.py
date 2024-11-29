from pathlib import Path

from ..settings import get_settings
from ._codegen import generate_modules, ruff_check
from ._metadata import WithMetadata as WithMetadata
from .user import APIKey, User

if get_settings().generate_models:
    import openai.types.beta.assistant
    import openai.types.beta.thread
    import openai.types.beta.threads.message
    import openai.types.beta.threads.run
    import openai.types.beta.threads.runs.run_step
    import openai.types.file_object

    generate_modules(
        openai.types.beta.assistant,
        openai.types.beta.thread,
        openai.types.beta.threads.message,
        openai.types.beta.threads.run,
        openai.types.beta.threads.runs.run_step,
        openai.types.file_object,
    )
    ruff_check(Path(__file__).parent / "generated")

from .generated.assistant import Assistant
from .generated.file_object import FileObject
from .generated.message import Message
from .generated.run import Run
from .generated.run_step import RunStep
from .generated.thread import Thread

__all__ = [
    "APIKey",
    "User",
    "Assistant",
    "Message",
    "Run",
    "RunStep",
    "Thread",
    "FileObject",
]
