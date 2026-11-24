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
async def test_timeout_uses_at_most_one_backup_stream_and_reports_a_second_timeout(monkeypatch):
    urls = []

    def reply(request):
        urls.append(request.url.path)
        raise httpx.ReadTimeout("simulated timeout", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)
    with pytest.raises(llm_service.GeminiStreamInterrupted, match="timeout"):
        async for _ in llm_service.stream_gemini_messages([{"role": "user", "content": "Tra cứu học phí"}]):
            pytest.fail("Timeout returned incomplete text")
    assert len(urls) == 2
    assert urls[-1].endswith(":streamGenerateContent")


@pytest.mark.asyncio
async def test_chat_retry_prefers_native_protocol(monkeypatch):
    paths = []

    def reply(request):
        paths.append(request.url.path)
        return httpx.Response(200, stream=GeminiChunks(
            sse({"candidates": [{"content": {"parts": [{"text": "Phản hồi đầy đủ"}]}, "finishReason": "STOP"}]}),
        ))

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)
    tokens = [
        token async for token in llm_service.stream_gemini_messages(
            [{"role": "user", "content": "Thử lại câu hỏi cũ"}], prefer_native=True,
        )
    ]
    assert tokens == ["Phản hồi đầy đủ"]
    assert len(paths) == 1 and paths[0].endswith(":streamGenerateContent")


@pytest.mark.asyncio
async def test_complete_response_uses_native_json_and_skips_thought(monkeypatch):
    requests = []

    def reply(request):
        requests.append(request)
        return httpx.Response(200, json={"candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [
                {"text": "Không hiển thị", "thought": True},
                {"text": "Trả lời "},
                {"text": "đầy đủ."},
            ]},
        }]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)
    tokens = llm_service.stream_gemini_messages(
        [{"role": "user", "content": "Tìm hiểu xét tuyển"}], complete_response=True,
    )
    assert [token async for token in tokens] == ["Trả lời đầy đủ."]
    assert len(requests) == 1 and requests[0].url.path.endswith(":generateContent")


@pytest.mark.asyncio
@pytest.mark.parametrize("backup_finished", [True, False])
async def test_complete_response_never_yields_partial_attempts(monkeypatch, backup_finished):
    paths = []

    def reply(request):
        paths.append(request.url.path)
        if len(paths) == 1:
            return httpx.Response(200, json={"candidates": [{
                "finishReason": "MAX_TOKENS",
                "content": {"parts": [{"text": "Câu trả lời dang dở"}]},
            }]})
        frames = [
            sse({"choices": [{"delta": {"content": "Kết quả "}}]}),
            sse({"choices": [{"delta": {"content": "đầy đủ."}}]}),
        ]
        if backup_finished:
            frames.append(sse({"choices": [{"delta": {}, "finish_reason": "stop"}]}))
        return httpx.Response(200, stream=GeminiChunks(*frames))

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)
    tokens = llm_service.stream_gemini_messages(
        [{"role": "user", "content": "So sánh các trường"}], complete_response=True,
    )
    async with aclosing(tokens):
        if backup_finished:
            assert [token async for token in tokens] == ["Kết quả đầy đủ."]
        else:
            with pytest.raises(llm_service.GeminiStreamInterrupted, match="connection"):
                await anext(tokens)
    assert len(paths) == 2 and paths[-1].endswith("/chat/completions")


@pytest.mark.asyncio
async def test_complete_response_does_not_retry_a_safety_block(monkeypatch):
    paths = []

    def reply(request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", lambda **kwargs: client)
    tokens = llm_service.stream_gemini_messages(
        [{"role": "user", "content": "Câu hỏi bị chặn"}], complete_response=True,
    )
    async with aclosing(tokens):
        with pytest.raises(llm_service.GeminiStreamInterrupted, match="blocked"):
            await anext(tokens)
    assert len(paths) == 1


@pytest.mark.asyncio
async def test_empty_recommendations_report_missing_matches_without_streaming_gemini(monkeypatch):
    from app.agent import service

    async def graph_result(*args, **kwargs):
        yield "values", {
            "intent": "RECOMMEND",
            "slots": {"student_score": 27.0, "student_group_code": "A00", "preferred_city": "TP.HCM"},
            "portfolio": {"reach": [], "target": [], "safe": []},
            "final_text": "READY_FOR_PORTFOLIO_STREAM",
        }

    def unexpected_gemini(*args, **kwargs):
        pytest.fail("The answer should report the empty recommendation result directly")

    advisor = CareerAdvisoryService()
    monkeypatch.setattr(advisor.app, "astream", graph_result)
    monkeypatch.setattr(service, "stream_gemini_messages", unexpected_gemini)
    events = [item async for item in advisor.run_advisory_flow("Tôi thi 27 điểm A00 ở HCM nên học ngành và trường nào")]
    assert [event["type"] for event in events] == ["token", "done"]
    assert "27 điểm, tổ hợp A00, TP.HCM" in events[0]["token"]
    assert "#huong-nghiep" in events[0]["token"]


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

    async def generate(messages, *, prefer_native, **kwargs):
        observed.extend(messages)
        assert prefer_native
        yield "Thông tin "
        await allow_finish.wait()
        yield "học phí."

    monkeypatch.setattr(graph, "classify_intent", classify)
    monkeypatch.setattr(graph, "extract_slots_with_llm", extract)
    monkeypatch.setattr(graph, "execute_query_async", query)
    monkeypatch.setattr(graph, "stream_gemini_messages", generate)
    events = CareerAdvisoryService().run_advisory_flow(
        "Học phí Trường thử?", session_id="streaming-lookup-test", prefer_native=True,
    )
    async with aclosing(events):
        assert await asyncio.wait_for(anext(events), 3) == {"type": "token", "token": "Thông tin "}
        assert "24680000" in observed[1]["content"]
        allow_finish.set()
        assert [event async for event in events] == [
            {"type": "token", "token": "học phí."},
            {"type": "done", "full_reply": "Thông tin học phí."},
        ]
