from fastapi import FastAPI

from . import __version__
from .routing import OAIRouter

STREAMING_RESPONSE_EXAMPLE = """\
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0125", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"role":"assistant","content":""},"logprobs":null,"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0125", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"content":"Hello"},"logprobs":null,"finish_reason":null}]}

....

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0125", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{},"logprobs":null,"finish_reason":"stop"}]}

data: [DONE]
"""


class FastOAI(FastAPI):
    def __init__(self, *, title="FastOAI", version=__version__, **kwargs):
        super().__init__(title=title, version=version, **kwargs)
        self.router: OAIRouter = OAIRouter()
        self.setup()

    def post_chat_completions(self, *args, **kwargs):
        if len(kwargs) > 0 or (len(args) + len(kwargs)) == 0:
            def decorator(func):
                return self.router.post_chat_completions(**kwargs)(func)
            return decorator
        return self.router.post_chat_completions(args[0])
    create_chat_completions = post_chat_completions

    def get_models(self, *args, **kwargs):
        if len(kwargs) > 0 or (len(args) + len(kwargs)) == 0:
            def decorator(func):
                return self.router.get_models(**kwargs)(func)
            return decorator
        return self.router.get_models(args[0])
