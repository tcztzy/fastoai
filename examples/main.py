from contextlib import asynccontextmanager

from fastoai import FastOAI
from fastoai.routers.ollama import router
from fastoai.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan():
    yield
    settings.session.close()


app = FastOAI(root_path="/v1", lifespan=lifespan)

# Order matters, you should firstly define your own entrypoint functions, then
# include the existing router in order to override the original process with
# yours
app.include_router(router)
