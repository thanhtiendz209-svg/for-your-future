import unittest,json
from unittest.mock import patch
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI,HTTPException
from fastapi.testclient import TestClient
from app.core.models_db import Base,User,ChatMessage
from app.core.database import get_db
from app.core.security import create_access_token
from app.modules.auth.service import get_current_user
from app.modules.consultation.history_router import router
from app.modules.consultation.history_migration import ensure_chat_owner

class ChatTests(unittest.TestCase):
 def setUp(self):
  self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
  Base.metadata.create_all(self.engine);self.Session=sessionmaker(bind=self.engine)
  with self.Session() as db:
   db.add_all([User(user_id='alice',email='alice@test',password_hash='x',role='admin'),User(user_id='bob',email='bob@test',password_hash='x',role='student')]);db.commit()
  self.app=FastAPI();self.app.include_router(router,prefix='/api/v1');self.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(user_id='alice')
  def database():
   with self.Session() as db:yield db
  self.app.dependency_overrides[get_db]=database
  self.patch=patch('app.modules.consultation.history_router.SessionLocal',self.Session);self.patch.start();self.client=TestClient(self.app)
 def tearDown(self):self.patch.stop();self.engine.dispose()
 def create(self):return self.client.post('/api/v1/chat/sessions').json()['session_id']
 def test_admin_without_student_profile_can_create_and_persist_greeting(self):
  sid=self.create();r=self.client.post(f'/api/v1/chat/sessions/{sid}/messages/stream',json={'prompt':'Xin chào'})
  self.assertEqual(r.status_code,200,r.text);self.assertIn('[DONE]',r.text)
  rows=self.client.get(f'/api/v1/chat/sessions/{sid}/messages').json();self.assertEqual([m['role'] for m in rows],['user','assistant']);self.assertIn('Chào bạn',rows[1]['content'])
  self.assertEqual(self.client.get('/api/v1/chat/sessions').json()[0]['title'],'Xin chào')
 def test_history_is_private(self):
  sid=self.create();self.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(user_id='bob')
  self.assertEqual(self.client.get('/api/v1/chat/sessions').json(),[])
  for path in [f'/{sid}/messages']:
   self.assertEqual(self.client.get('/api/v1/chat/sessions'+path).status_code,404)
  self.assertEqual(self.client.post(f'/api/v1/chat/sessions/{sid}/messages/stream',json={'prompt':'Xin chào'}).status_code,404)
 def test_multi_turn_context_and_stream_saved(self):
  # Use a real authenticated ORM user so the test detects stale session access.
  del self.app.dependency_overrides[get_current_user]
  self.client.headers["Authorization"] = f"Bearer {create_access_token('alice')}"
  sid = self.create()
  path = f'/api/v1/chat/sessions/{sid}/messages'
  greeting = self.client.post(path + '/stream', json={'prompt': 'Xin chào'})
  self.assertEqual(greeting.status_code, 200, greeting.text)
  received = []

  async def reply(**kwargs):
   received.append(kwargs)
   yield {'type': 'token', 'token': 'Kết quả **có nguồn**'}

  with patch('app.modules.consultation.history_router.career_advisory_service.run_advisory_flow', new=reply):
   for prompt in ('Ngành công nghệ thông tin', 'Còn học phí thì sao?'):
    response = self.client.post(path + '/stream', json={'prompt': prompt})
    self.assertEqual(response.status_code, 200, response.text)
    self.assertIn('Kết quả **có nguồn**', response.text)
    self.assertIn('[DONE]', response.text)

  self.assertEqual(received[-1]['profile_data']['student_id'], 'alice')
  self.assertIn({'role': 'user', 'content': 'Ngành công nghệ thông tin'}, received[-1]['history'])
  self.assertTrue(any(message['role'] == 'assistant' for message in received[-1]['history']))
  rows = self.client.get(path).json()
  self.assertEqual(len(rows), 6)
  self.assertEqual(rows[-1]['content'], 'Kết quả **có nguồn**')
 def test_missing_profile_becomes_saved_actionable_message(self):
  sid=self.create()
  async def missing(*args):raise HTTPException(422,'Vui lòng hoàn thành RIASEC')
  with patch('app.modules.consultation.history_router.chat_recommend_stream',new=missing):
   r=self.client.post(f'/api/v1/chat/sessions/{sid}/messages/stream',json={'prompt':'Tư vấn giúp tôi'})
  self.assertIn('RIASEC',r.text)
  self.assertIn('RIASEC',self.client.get(f'/api/v1/chat/sessions/{sid}/messages').json()[-1]['content'])
 def test_followup_overrides_city_and_keeps_prior_score(self):
  from app.modules.graphrag.profile_context import build_profile_intent
  p=SimpleNamespace(academic={'subject_scores':{}},background={},health={},gender='Other',latest_riasec={'result_code':'RIA'},latest_mbti=None)
  intent=build_profile_intent(p,'Chuyển sang Hà Nội nhé',2026,['Em thi A00 được 26 điểm ở TP.HCM, ngân sách 30 triệu'])
  self.assertEqual(intent.student_score,26)
  self.assertEqual(intent.preferred_city,'Hà Nội')
  self.assertEqual(intent.max_annual_budget,30000000)
 def test_migration_can_run_twice(self):ensure_chat_owner(self.engine);ensure_chat_owner(self.engine)
 def test_migration_upgrades_legacy_table_and_backfills(self):
  from sqlalchemy import text
  legacy=create_engine('sqlite://')
  with legacy.begin() as db:
   db.execute(text('CREATE TABLE users (user_id VARCHAR(36) PRIMARY KEY)'))
   db.execute(text("INSERT INTO users VALUES ('old-user')"))
   db.execute(text('CREATE TABLE chat_sessions (session_id VARCHAR(36) PRIMARY KEY,student_id VARCHAR(36))'))
   db.execute(text("INSERT INTO chat_sessions VALUES ('old-thread','old-user')"))
  ensure_chat_owner(legacy);ensure_chat_owner(legacy)
  with legacy.connect() as db:self.assertEqual(db.execute(text('SELECT owner_user_id FROM chat_sessions')).scalar(),'old-user')
  legacy.dispose()
if __name__=='__main__':unittest.main()
