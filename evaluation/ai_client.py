import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AI_REQUEST_TIMEOUT_SECONDS = 45


def _extract_text(payload):
    if isinstance(payload, str):
        return payload
    if isinstance(payload, list):
        for item in payload:
            text = _extract_text(item)
            if text:
                return text
        return ""
    if isinstance(payload, dict):
        for key in ("text", "response", "content", "generated_text", "output", "result"):
            if key in payload:
                text = _extract_text(payload[key])
                if text:
                    return text
    return ""


def generate_evaluation_text(*, endpoint, model, prompt):
    body = json.dumps({"model": model, "prompt": prompt}).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=AI_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AI呼び出しに失敗しました: HTTP {error.code} {detail}") from error
    except URLError as error:
        raise RuntimeError(f"AI呼び出しに失敗しました: {error.reason}") from error
    except (TimeoutError, socket.timeout) as error:
        raise RuntimeError("AI評価の応答がタイムアウトしました。少し時間をおいて再実行してください。") from error

    text = _extract_text(payload).strip()
    if not text:
        raise RuntimeError("AI応答から評価文を取得できませんでした。")
    return text
