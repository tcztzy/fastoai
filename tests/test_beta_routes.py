import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from fastoai import app
from fastoai.models import APIKey, User
from fastoai.settings import Settings, get_settings


class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


@pytest.fixture(name="settings", scope="module")
def settings_fixture():
    return Settings(  # type: ignore
        database_url="sqlite+aiosqlite://",
        base_url="http://testserver",
    )


async def setup_database(session: AsyncSession):
    user = User(name="First Last", password="password")
    api_key = APIKey(user=user)  # type: ignore
    session.add(user)
    await session.commit()
    session.add(api_key)
    await session.commit()


@pytest.fixture(name="session", scope="module")
async def session_fixture(settings: Settings):
    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        await setup_database(session)
        yield session


@pytest.fixture(name="client", scope="module")
async def client_fixture(settings: Settings, session: AsyncSession):
    def get_settings_override():
        return settings

    app.dependency_overrides[get_settings] = get_settings_override
    key = (await session.exec(select(APIKey))).one()
    async with AsyncClient(
        base_url=settings.base_url,
        transport=ASGITransport(app=app),
    ) as ac:
        yield AsyncOpenAI(api_key=key.id, base_url=settings.base_url, http_client=ac)
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_beta_routes(client: AsyncOpenAI):
    assistants = await client.beta.assistants.list()
    assert assistants.data == []
    assistant = await client.beta.assistants.create(
        model="gpt-4o-mini",
        tools=[],  # TODO: tools should be optional
    )
    await client.beta.assistants.delete(assistant.id)
