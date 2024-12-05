import pytest
from openai import AsyncOpenAI


@pytest.mark.anyio
async def test_beta_routes(client: AsyncOpenAI, user_id: str):
    assistants = await client.beta.assistants.list()
    assert assistants.data == []
    assistant = await client.beta.assistants.create(
        model="gpt-4o-mini",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                    },
                },
            },
            {"type": "code_interpreter"},
        ],
        metadata={"user_id": user_id},
    )
    assert len(assistant.tools) == 2
    assert assistant.metadata == {"user_id": user_id}
    await client.beta.assistants.delete(assistant.id)
