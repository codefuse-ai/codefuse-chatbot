from fastchat.conversation import Conversation
from .base import *
from fastchat import conversation as conv
import sys
import os
import json
from typing import List, Dict
from loguru import logger

log_verbose = os.environ.get("log_verbose", False)

# MiniMax supported models
MINIMAX_MODELS = ["MiniMax-M2.7", "MiniMax-M2.7-highspeed"]

# Default base URL for MiniMax OpenAI-compatible API
MINIMAX_DEFAULT_BASE_URL = "https://api.minimax.io/v1"


def _clamp_temperature(temperature: float) -> float:
    """Clamp temperature to MiniMax's valid range (0.0, 1.0].

    MiniMax does not accept temperature=0. Values at or below 0 are
    clamped to a small positive epsilon; values above 1.0 are clamped to 1.0.
    """
    if temperature is None:
        return 1.0
    if temperature <= 0:
        return 0.01
    if temperature > 1.0:
        return 1.0
    return temperature


class MiniMaxWorker(ApiModelWorker):
    """MiniMax model worker using the OpenAI-compatible Chat Completions API.

    Supports MiniMax-M2.7 and MiniMax-M2.7-highspeed models via the
    standard /v1/chat/completions endpoint at api.minimax.io.

    Configuration:
        api_key: MiniMax API key (or set MINIMAX_API_KEY env var)
        api_base_url: API base URL (default: https://api.minimax.io/v1)
        version: Model name (default: MiniMax-M2.7)
    """

    def __init__(
        self,
        *,
        model_names: List[str] = ["minimax-api"],
        controller_addr: str = None,
        worker_addr: str = None,
        version: str = "MiniMax-M2.7",
        **kwargs,
    ):
        kwargs.update(
            model_names=model_names,
            controller_addr=controller_addr,
            worker_addr=worker_addr,
        )
        kwargs.setdefault("context_len", 204800)
        super().__init__(**kwargs)
        self.version = version

    def do_chat(self, params: ApiChatParams) -> Dict:
        params.load_config(self.model_names[0])

        api_key = params.api_key or os.environ.get("MINIMAX_API_KEY", "")
        base_url = (params.api_base_url or MINIMAX_DEFAULT_BASE_URL).rstrip("/")
        url = f"{base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        temperature = _clamp_temperature(params.temperature)

        data = {
            "model": params.version or self.version,
            "messages": params.messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": params.max_tokens or 1024,
        }

        if log_verbose:
            logger.info(f"{self.__class__.__name__}:url: {url}")
            logger.info(f"{self.__class__.__name__}:data: {data}")

        with get_httpx_client() as client:
            response = client.stream("POST", url, headers=headers, json=data)
            with response as r:
                text = ""
                for line in r.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    if error := chunk.get("error"):
                        data = {
                            "error_code": 500,
                            "text": error.get("message", str(error)),
                            "error": error,
                        }
                        self.logger.error(
                            f"MiniMax API error: {data}"
                        )
                        yield data
                        return

                    if choices := chunk.get("choices"):
                        delta = choices[0].get("delta", {})
                        if content := delta.get("content", ""):
                            text += content
                            yield {"error_code": 0, "text": text}

    def get_embeddings(self, params):
        print("embedding")
        print(params)

    def make_conv_template(
        self, conv_template: str = None, model_path: str = None
    ) -> Conversation:
        return conv.Conversation(
            name=self.model_names[0],
            system_message="You are MiniMax, a helpful AI assistant.",
            messages=[],
            roles=["user", "assistant"],
            sep="\n### ",
            stop_str="###",
        )


if __name__ == "__main__":
    import uvicorn
    from server.utils import MakeFastAPIOffline
    from fastchat.serve.model_worker import app

    worker = MiniMaxWorker(
        controller_addr="http://127.0.0.1:20001",
        worker_addr="http://127.0.0.1:21002",
    )
    sys.modules["fastchat.serve.model_worker"].worker = worker
    MakeFastAPIOffline(app)
    uvicorn.run(app, port=21002)
