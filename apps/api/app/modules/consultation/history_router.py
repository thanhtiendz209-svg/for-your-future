"""Account-owned conversations, reusing the existing grounded recommendation stream."""
import json
from contextlib import aclosing
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
from app.modules.graphrag.router import extract_user_profile_data

logger = logging.getLogger("graphrag.history_router")
router=APIRouter(prefix='/chat/sessions',tags=['Chat history'])

class MessageRequest(BaseModel):
    prompt: str=Field(...,min_length=1,max_length=6000)
    target_year: int=Field(2026,ge=2024,le=2030)
    continuation: str | None = Field(default=None, max_length=6000)

def owned(db,sid,user):
    thread=db.query(ChatSession).filter(ChatSession.session_id==sid,or_(ChatSession.owner_user_id==user.user_id,and_(ChatSession.owner_user_id.is_(None),ChatSession.student_id==user.user_id))).first()
    if not thread:raise HTTPException(404,'Không tìm thấy cuộc trò chuyện.')
    return thread

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
    owned(db,sid,user)
    return [{'message_id':m.message_id,'role':m.role,'content':m.content,'created_at':m.created_at,'evidence':m.evidence or []} for m in db.query(ChatMessage).filter(ChatMessage.session_id==sid).order_by(ChatMessage.created_at,ChatMessage.message_id)]

@router.post('/{sid}/messages/stream')
async def send(sid: str, req: MessageRequest, user=Depends(get_current_user), db: Session=Depends(get_db)):
    thread = owned(db, sid, user)
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(422, 'Vui lòng nhập tin nhắn.')
    continuation = (req.continuation or "").strip() or None
    history = (
        db.query(ChatMessage).filter(ChatMessage.session_id == sid)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.message_id.desc()).limit(12).all()[::-1]
    )
    history_data = [{'role': message.role, 'content': message.content[:5000]} for message in history if message.content]
    is_greeting = not continuation and prompt.lower().strip('!?. ') in ('xin chào', 'chào', 'hello', 'hi')
    # Request sessions and their ORM objects are closed before the response streams.
    profile_data = None if is_greeting else extract_user_profile_data(db, user)
    if not history:
        thread.title = prompt[:80]
    user_message = 'Viết tiếp câu trả lời' if continuation else prompt
    db.add(ChatMessage(session_id=sid, role='user', content=user_message))
    db.commit()

    async def events():
        parts = []
        evidence = []
        completed = False
        reason = None
        interruption = None

        def event(data):
            return f'data: {json.dumps(data, ensure_ascii=False)}\n\n'

        try:
            yield ': ready\n\n'
            if is_greeting:
                answer = 'Chào bạn! Tôi có thể giúp bạn tìm ngành phù hợp, tra cứu trường và học phí, hoặc cân nhắc nguyện vọng. Bạn đang quan tâm đến ngành hay trường nào?'
                parts.append(answer)
                yield event({'type': 'token', 'token': answer})
                completed = True
            else:
                flow = career_advisory_service.run_advisory_flow(
                    prompt=prompt,
                    session_id=f'sess_{sid}',
                    history=history_data + [{'role': 'user', 'content': prompt}],
                    profile_data=profile_data,
                    continuation=continuation,
                )
                async with aclosing(flow):
                    async for item in flow:
                        kind = item.get('type')
                        if kind == 'token':
                            parts.append(item['token'])
                        elif kind == 'portfolio':
                            evidence.append(item)
                        elif kind == 'interrupted':
                            reason = item.get('reason') or 'connection'
                            break
                        elif kind == 'done':
                            completed = True
                            break
                        elif kind not in ('intent', 'clarification'):
                            continue
                        yield event(item)
        except Exception:
            logger.exception("Error in advisory streaming flow")
            reason = 'connection'
        finally:
            # Keep the reply and its recovery details when generation or the client disconnects.
            answer = ''.join(parts).strip()
            if reason or not completed or not answer:
                interruption = {
                    'type': 'interrupted', 'reason': reason or 'connection',
                    'prompt': prompt, 'target_year': req.target_year,
                }
                evidence.append(interruption)
            with SessionLocal() as save:
                save.add(ChatMessage(session_id=sid, role='assistant', content=answer, evidence=evidence))
                save.commit()

        if interruption:
            yield event({'type': 'interrupted', 'reason': interruption['reason']})
        else:
            yield 'data: [DONE]\n\n'

    return StreamingResponse(
        events(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no'},
    )
