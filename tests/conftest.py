import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, StaticPool, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastoai import app
from fastoai.dependencies import get_session, get_settings
from fastoai.models.key import Key
from fastoai.models.organization import Organization
from fastoai.models.organization_user import OrganizationUser, OrganizationUserRole
from fastoai.models.project import Project
from fastoai.models.project_user import ProjectUser, ProjectUserRole
from fastoai.models.user import User
from fastoai.settings import Settings


class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


@pytest.fixture(name="settings", scope="module")
def settings_fixture():
    settings = Settings(  # type: ignore
        database_url="sqlite+aiosqlite://",
        base_url="http://testserver",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    yield settings
    app.dependency_overrides.clear


async def setup_database(session: AsyncSession):
    user = User(name="First Last", email="test@example.com", password="password")
    organization = Organization(name="Personal")
    organization_user = OrganizationUser(
        id=user.id,
        organization_id=organization.id,
        role=OrganizationUserRole.OWNER,
    )
    project = Project(name="Test Project", organization_id=organization.id)
    project_user = ProjectUser(
        name=user.name,
        email=user.email,
        role=ProjectUserRole.OWNER,
        id=user.id,
        project_id=project.id,
    )
    api_key = Key(
        user_id=project_user.id,
        project_id=project.id,
    )
    session.add(user)
    session.add(organization)
    session.add(organization_user)
    session.add(project)
    session.add(project_user)
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
        app.dependency_overrides[get_session] = lambda: session
        yield session
        app.dependency_overrides.clear()


@pytest.fixture(name="user_id", scope="module")
async def user_fixture(session: AsyncSession) -> str:
    return (await session.exec(select(User))).one().id


@pytest.fixture(name="api_key", scope="module")
async def api_key_fixture(session: AsyncSession) -> str:
    return (await session.exec(select(Key))).one().id


@pytest.fixture(name="http_client", scope="module")
async def http_client_fixture(settings: Settings):
    app.dependency_overrides[get_settings] = lambda: settings
    async with AsyncClient(
        base_url=settings.base_url,
        transport=ASGITransport(app=app),
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(name="client", scope="module")
async def client_fixture(settings: Settings, http_client: AsyncClient, api_key: str):
    yield AsyncOpenAI(
        api_key=api_key, base_url=settings.base_url, http_client=http_client
    )
