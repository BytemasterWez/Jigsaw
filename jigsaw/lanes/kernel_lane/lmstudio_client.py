from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


class LMStudioError(RuntimeError):
    pass


@dataclass
class LMStudioResponse:
    model: str
    raw_response: dict[str, Any]
    parsed_content: dict[str, Any]


class LMStudioClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("JIGSAW_LMSTUDIO_BASE_URL") or "http://127.0.0.1:1234/v1").rstrip("/")
        self.model = model or os.getenv("JIGSAW_LMSTUDIO_MODEL")
        self.timeout_seconds = timeout_seconds

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LMStudioError(f"LM Studio HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise LMStudioError(f"Unable to reach LM Studio at {self.base_url}: {exc.reason}") from exc
        except (TimeoutError, OSError) as exc:
            raise LMStudioError(f"LM Studio request to {self.base_url}{path} timed out or failed: {exc}") from exc

    def is_available(self) -> bool:
        try:
            self.list_models()
        except LMStudioError:
            return False
        return True

    def list_models(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/models")
        return payload.get("data", [])

    def resolve_model(self) -> str:
        if self.model:
            return self.model
        models = self.list_models()
        if not models:
            raise LMStudioError("LM Studio responded but no local model is loaded.")
        model_id = models[0].get("id")
        if not model_id:
            raise LMStudioError("LM Studio model listing did not include a usable model id.")
        self.model = model_id
        return model_id

    def create_structured_chat_completion(
        self,
        *,
        system_prompt: str | None,
        user_prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> LMStudioResponse:
        model = self.resolve_model()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.get("title", "kernel_output"),
                    "strict": True,
                    "schema": response_schema,
                },
            },
        }
        raw_response = self._request("POST", "/chat/completions", payload)
        choices = raw_response.get("choices") or []
        if not choices:
            raise LMStudioError("LM Studio returned no choices for the structured completion.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise LMStudioError("LM Studio returned an empty structured completion payload.")
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LMStudioError(f"LM Studio returned non-JSON structured content: {content}") from exc
        return LMStudioResponse(model=model, raw_response=raw_response, parsed_content=parsed_content)
