"""Account-owned conversations, reusing the existing grounded recommendation stream."""
import asyncio
import json
from contextlib import aclosing
from uuid import UUID, uuid4
from anyio import CancelScope
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.models_db import ChatSession, ChatMessage, StudentProfile
from app.modules.auth.service import get_current_user
import logging
from app.agent.service import career_advisory_service
from app.modules.graphrag.llm_service import fallback_portfolio_text
from app.modules.graphrag.router import extract_user_profile_data

logger = logging.getLogger("graphrag.history_router")
router=APIRouter(prefix='/chat/sessions',tags=['Chat history'])
SSE_KEEPALIVE_SECONDS = 8.0


class AccountChatResponse(StreamingResponse):
    async def stream_response(self, send):
        try:
            await super().stream_response(send)
        finally:
            # A disconnect can interrupt the send of an already-yielded frame.
            with CancelScope(shield=True):
                await self.body_iterator.aclose()


async def advisory_items_with_keepalive(flow):
    items = asyncio.Queue(maxsize=1)

    async def consume():
        try:
            async with aclosing(flow):
                async for item in flow:
                    await items.put(item)
        except Exception as error:
            await items.put(error)
        else:
            await items.put(None)

    # Run the upstream iterator in one task so streaming contexts stay in their owning task.
    producer = asyncio.create_task(consume())
    loop = asyncio.get_running_loop()
    heartbeat_at = loop.time() + SSE_KEEPALIVE_SECONDS
    try:
        while True:
            remaining = heartbeat_at - loop.time()
            if remaining <= 0:
                yield None
                heartbeat_at = loop.time() + SSE_KEEPALIVE_SECONDS
                continue
            try:
                item = await asyncio.wait_for(items.get(), timeout=remaining)
            except asyncio.TimeoutError:
                if producer.done():
                    producer.result()
                continue
            if item is None:
                return
            if isinstance(item, Exception):
                raise item
            yield item
    finally:
        producer.cancel()
        with CancelScope(shield=True):
            await asyncio.gather(producer, return_exceptions=True)

class MessageRequest(BaseModel):
    prompt: str=Field(...,min_length=1,max_length=6000)
    target_year: int=Field(2026,ge=2024,le=2030)
    message_id: UUID | None = None

def owned(db, sid, user_id, *, lock=False):
    query = db.query(ChatSession).filter(
        ChatSession.session_id == sid,
        or_(ChatSession.owner_user_id == user_id,
            and_(ChatSession.owner_user_id.is_(None), ChatSession.student_id == user_id)),
    )
    thread = (query.with_for_update() if lock else query).first()
    if not thread:raise HTTPException(404,'Không tìm thấy cuộc trò chuyện.')
    return thread

def recent_messages(db, sid, limit=12):
    return (db.query(ChatMessage).filter(ChatMessage.session_id == sid)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.message_id.desc())
            .limit(limit).all()[::-1])


def latest_reply(history, question_id):
    if history and history[-1].message_id == question_id:
        return None
    if (len(history) >= 2 and history[-2].message_id == question_id
            and history[-1].role == 'assistant'):
        return history[-1]
    raise HTTPException(409, 'Cuộc trò chuyện đã có câu hỏi mới. Hãy mở lại lịch sử để đồng bộ.')


def event(data):
    return f'data: {json.dumps(data, ensure_ascii=False)}\n\n'


def completed_events(answer, details):
    for item in details:
        yield event(item)
    yield event({'type': 'token', 'token': answer})
    yield 'data: [DONE]\n\n'

def session_item(t):
    return {'session_id':t.session_id,'title':t.title,'started_at':t.started_at}

@router.get('')
def sessions(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return [session_item(t) for t in db.query(ChatSession).filter(or_(ChatSession.owner_user_id==user.user_id,and_(ChatSession.owner_user_id.is_(None),ChatSession.student_id==user.user_id))).order_by(ChatSession.started_at.desc()).all()]

@router.post('',status_code=201)
def create(user=Depends(get_current_user),db:Session=Depends(get_db)):
    profile=db.get(StudentProfile,user.user_id)
    t=ChatSession(owner_user_id=user.user_id,student_id=user.user_id if profile else None,title='Cuộc trò chuyện mới')
    db.add(t);db.commit();db.refresh(t)
    return session_item(t)

@router.get('/{sid}/messages')
def messages(sid:str,user=Depends(get_current_user),db:Session=Depends(get_db)):
    owned(db,sid,user.user_id)
    return [{'message_id':m.message_id,'role':m.role,'content':m.content,'created_at':m.created_at,'evidence':m.evidence or []} for m in db.query(ChatMessage).filter(ChatMessage.session_id==sid).order_by(ChatMessage.created_at,ChatMessage.message_id)]

@router.post('/{sid}/messages/stream')
async def send(sid: str, req: MessageRequest, user=Depends(get_current_user), db: Session=Depends(get_db)):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(422, 'Vui lòng nhập tin nhắn.')
    user_id = user.user_id
    question_id = str(req.message_id or uuid4())
    thread = owned(db, sid, user_id, lock=True)
    existing = db.get(ChatMessage, question_id) if req.message_id else None
    prefer_native = existing is not None
    history = recent_messages(db, sid, limit=13 if existing else 12)
    cached = None
    if existing:
        if existing.session_id != sid or existing.role != 'user' or existing.content != prompt:
            raise HTTPException(409, 'Không thể thử lại câu hỏi này.')
        answer = latest_reply(history, question_id)
        if answer:
            cached = (answer.content, answer.evidence or [])
        else:
            # The current question is appended explicitly when calling the agent.
            history = history[:-1]
    else:
        if not history:
            thread.title = prompt[:80]
        db.add(ChatMessage(message_id=question_id, session_id=sid, role='user', content=prompt))

    history_data = [{'role': message.role, 'content': message.content[:5000]} for message in history if message.content]
    is_greeting = prompt.lower().strip('!?. ') in ('xin chào', 'chào', 'hello', 'hi')
    # Request sessions and their ORM objects are closed before the response streams.
    profile_data = None if is_greeting or cached else extract_user_profile_data(db, user)
    db.commit()

    async def events():
        yield ': ready\n\n'
        if cached:
            for frame in completed_events(*cached):
                yield frame
            return

        parts = []
        details = []
        completed = False
        reason = None

        try:
            if is_greeting:
                parts.append('Chào bạn! Tôi có thể giúp bạn tìm ngành phù hợp, tra cứu trường và học phí, hoặc cân nhắc nguyện vọng. Bạn đang quan tâm đến ngành hay trường nào?')
                completed = True
            else:
                flow = career_advisory_service.run_advisory_flow(
                    prompt=prompt,
                    session_id=f'sess_{sid}',
                    history=history_data + [{'role': 'user', 'content': prompt}],
                    profile_data=profile_data,
                    prefer_native=prefer_native,
                    complete_response=True,
                )
                async with aclosing(advisory_items_with_keepalive(flow)) as items:
                    async for item in items:
                        if item is None:
                            yield ': keepalive\n\n'
                            continue
                        kind = item.get('type')
                        if kind == 'token':
                            parts.append(item['token'])
                            if len(parts) == 1:
                                yield event({'type': 'composing'})
                        elif kind in ('portfolio', 'intent', 'clarification'):
                            details.append(item)
                        elif kind == 'interrupted':
                            reason = item.get('reason') or 'connection'
                            break
                        elif kind == 'done':
                            completed = True
                            break
        except Exception:
            logger.exception("Error in advisory streaming flow")
            reason = 'connection'

        answer = ''.join(parts).strip()
        evidence = [item for item in details if item['type'] == 'portfolio']
        if reason in ('busy', 'timeout', 'connection', 'length') and evidence:
            intent = next((item['data'] for item in details if item['type'] == 'intent'), {})
            lines = fallback_portfolio_text(evidence[-1]['data'], {
                'student_score': intent.get('student_score'),
                'student_group_code': intent.get('subject_group'),
            })
            if lines:
                logger.info("Recovered interrupted advisory using verified portfolio: reason=%s", reason)
                answer = ''.join(lines).strip()
                completed = True
                reason = None
        if reason or not completed or not answer:
            logger.warning("Advisory stream interrupted: reason=%s, has_text=%s, completed=%s",
                           reason or 'connection', bool(answer), completed)
            yield event({'type': 'interrupted', 'reason': reason or 'connection'})
            return

        try:
            with SessionLocal() as save:
                # A retry may overlap with the previous request finishing after the client lost its connection.
                owned(save, sid, user_id, lock=True)
                stored = latest_reply(recent_messages(save, sid, limit=2), question_id)
                if stored:
                    answer, details = stored.content, stored.evidence or []
                else:
                    save.add(ChatMessage(session_id=sid, role='assistant', content=answer, evidence=evidence))
                save.commit()
        except HTTPException:
            yield event({'type': 'interrupted', 'reason': 'superseded'})
            return
        except Exception:
            logger.exception("Could not save completed advisory reply")
            yield event({'type': 'interrupted', 'reason': 'connection'})
            return

        for frame in completed_events(answer, details):
            yield frame

    return AccountChatResponse(
        events(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no'},
    )
