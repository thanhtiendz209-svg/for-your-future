import asyncio
from contextlib import aclosing
import json

import httpx
import pytest

from app.agent import graph
from app.agent.service import CareerAdvisoryService
from app.modules.graphrag import llm_service


def sse(data):
    return f"data: {json.dumps(data)}\n\n".encode()


class GeminiChunks(httpx.AsyncByteStream):
    def __init__(self, *frames):
        self.frames = frames

    async def __aiter__(self):
        for frame in self.frames:
            yield frame


@pytest.mark.asyncio
@pytest.mark.parametrize("finish,reason", [("stop", None), ("length", "length"), ("overload", "busy"), (None, "connection")])
async def test_openai_stream_reports_partial_finish(monkeypatch, finish, reason):
    urls = []
    frames = [sse({"choices": [{"delta": {"content": "Phần đầu"}}]})]
    if finish == "overload":
        frames.append(sse({"error": {"code": 503, "status": "UNAVAILABLE"}}))
    elif finish:
        frames.append(sse({"choices": [{"delta": {}, "finish_reason": finish}]}))

    def reply(request):
        urls.append(request.url.path)
        return httpx.Response(200, stream=GeminiChunks(*frames))

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)

    tokens = llm_service.stream_gemini_messages([{"role": "user", "content": "Tra cứu học phí"}])
    async with aclosing(tokens):
        assert await anext(tokens) == "Phần đầu"
        if reason:
            with pytest.raises(llm_service.GeminiStreamInterrupted, match=reason):
                await anext(tokens)
        else:
            with pytest.raises(StopAsyncIteration):
                await anext(tokens)
    assert len(urls) == 1


@pytest.mark.asyncio
async def test_native_fallback_streams_before_any_text(monkeypatch):
    requests = []

    def reply(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503)
        return httpx.Response(200, stream=GeminiChunks(
            sse({"candidates": [{"content": {"parts": [{"text": "Một phần"}]}}]}),
            sse({"candidates": [{"content": {"parts": [{"text": " rồi thêm"}]}, "finishReason": "STOP"}]}),
        ))

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)
    tokens = [
        token async for token in llm_service.stream_gemini_messages(
            [
                {"role": "user", "content": "Tìm hiểu học phí"},
                {"role": "assistant", "content": "Phần trước"},
                {"role": "user", "content": "Chi phí ký túc xá thì sao?"},
            ]
        )
    ]
    assert tokens == ["Một phần", " rồi thêm"]
    assert requests[1].url.path.endswith(":streamGenerateContent")
    assert requests[1].url.params["alt"] == "sse"
    native = json.loads(requests[1].content)
    assert [(item["role"], item["parts"][0]["text"]) for item in native["contents"][:2]] == [
        ("user", "Tìm hiểu học phí"), ("model", "Phần trước"),
    ]


@pytest.mark.asyncio
async def test_lookup_yields_first_text_while_gemini_is_still_generating(monkeypatch):
    allow_finish = asyncio.Event()
    observed = []

    async def classify(prompt, history):
        return "LOOKUP"

    async def extract(prompt, history):
        return {"target_university": "Trường thử"}

    async def query(cypher, params):
        return [{"name": "Trường thử", "avg_tuition": 24680000}]

    async def generate(messages, **kwargs):
        observed.extend(messages)
        yield "Thông tin "
        await allow_finish.wait()
        yield "học phí."

    monkeypatch.setattr(graph, "classify_intent", classify)
    monkeypatch.setattr(graph, "extract_slots_with_llm", extract)
    monkeypatch.setattr(graph, "execute_query_async", query)
    monkeypatch.setattr(graph, "stream_gemini_messages", generate)
    events = CareerAdvisoryService().run_advisory_flow(
        "Học phí Trường thử?", session_id="streaming-lookup-test",
    )
    async with aclosing(events):
        assert await asyncio.wait_for(anext(events), 3) == {"type": "token", "token": "Thông tin "}
        assert "24680000" in observed[1]["content"]
        allow_finish.set()
        assert [event async for event in events] == [
            {"type": "token", "token": "học phí."},
            {"type": "done", "full_reply": "Thông tin học phí."},
        ]
