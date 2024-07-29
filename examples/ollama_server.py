from fastapi.responses import StreamingResponse
from fastoai import FastOAI
from fastoai.requests import CompletionCreateParams
from fastoai.routers.ollama import router
from openai import AsyncOpenAI

app = FastOAI(root_path="/v1")


@app.post_chat_completions
async def create_chat_completions(params: CompletionCreateParams):
    client = AsyncOpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
    response = await client.chat.completions.create(**params.model_dump())
    if params.stream:

        async def _stream():
            async for chunk in response:
                for choice in chunk.choices:
                    choice.delta.content += " [ollama]"
                yield f"data: {chunk.model_dump_json()}\n\n"
            else:
                yield "data: [DONE]\n\n"

        return StreamingResponse(_stream())
    return response


# Order matters, you should firstly define your own entrypoint functions, then
# include the existing router in order to override the original process with
# yours
app.include_router(router)
