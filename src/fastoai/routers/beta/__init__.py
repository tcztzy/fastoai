from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header

from .assistants import router as beta_router
from .messages import router as messages_router
from .run_steps import router as run_steps_router
from .runs import router as runs_router
from .threads import router as threads_router


def required_beta_header(
    _: Annotated[Literal["assistants=v2"], Header(alias="OpenAI-Beta")],
): ...


router = APIRouter(tags=["Assistants"], dependencies=[Depends(required_beta_header)])
router.include_router(beta_router)
router.include_router(threads_router)
router.include_router(messages_router)
router.include_router(runs_router)
router.include_router(run_steps_router)
