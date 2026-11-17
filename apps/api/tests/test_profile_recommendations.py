import unittest
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.modules.graphrag.profile_context import build_profile_intent
from app.modules.graphrag.router import router
from app.modules.auth.service import get_current_user
from app.core.database import get_db
from app.modules.graphrag.llm_service import build_portfolio_system_prompt
from app.modules.graphrag.recommender import build_portfolio_recommendations


def profile():
    return SimpleNamespace(academic={'subject_scores':{'Toán':0,'Vật lý':8,'Hóa học':9,'Tiếng Anh':10},'gpa_5_semesters':8.5},background={},health={},gender='Other',latest_riasec={'result_code':'SIA'},latest_mbti={'result_code':'INFJ'})


class ProfileRecommendationTests(unittest.TestCase):
    def test_saved_scores_zero_and_optional_data(self):
        intent=build_profile_intent(profile(),'Tư vấn giúp em',2026)
        self.assertEqual((intent.student_group_code,intent.student_score),('A01',18))
        self.assertEqual(intent.inferred_holland_code,'SIA')
        self.assertIsNone(intent.max_annual_budget)
        self.assertIsNone(intent.student_height)
        self.assertEqual(intent.profile_context['mbti'],'INFJ')

    def test_question_overrides_and_incomplete_group(self):
        intent=build_profile_intent(profile(),'Em thi khối A00 được 26 điểm, ngân sách 30 triệu',2026)
        self.assertEqual(intent.student_score,26)
        self.assertEqual(intent.student_group_code,'A00')
        self.assertEqual(intent.max_annual_budget,30000000)
        with self.assertRaises(HTTPException):
            build_profile_intent(profile(),'Em thi C00',2026)

    def test_gpa_does_not_replace_missing_exam_scores(self):
        p=profile();p.academic['subject_scores']={}
        with self.assertRaises(HTTPException) as err: build_profile_intent(p,'Tư vấn',2026)
        self.assertEqual(err.exception.status_code,422)

    def test_requires_saved_riasec(self):
        p=profile();p.latest_riasec=None
        with self.assertRaises(HTTPException): build_profile_intent(p,'Tư vấn',2026)

    def test_zero_budget_and_physical_traits(self):
        p=profile();p.background={'max_annual_tuition':0};p.health={'height_cm':160,'eye_degree_left':0,'eye_degree_right':2}
        intent=build_profile_intent(p,'Tư vấn',2026)
        self.assertEqual(intent.max_annual_budget,0)
        self.assertEqual(intent.student_eye_degree,2)
        self.assertEqual(intent.student_height,160)

    def test_llm_prompt_supports_skipped_budget(self):
        intent=build_profile_intent(profile(),'Tư vấn',2026)
        portfolio=build_portfolio_recommendations([],intent)
        text=build_portfolio_system_prompt(portfolio,'Tư vấn')
        self.assertIn('Chưa cung cấp',text)
        self.assertIn('INFJ',text)

    def client(self,authenticated=True):
        app=FastAPI();app.include_router(router,prefix='/api/v1')
        app.dependency_overrides[get_db]=lambda: object()
        if authenticated: app.dependency_overrides[get_current_user]=lambda: SimpleNamespace(user_id='account-a')
        return TestClient(app)

    def test_both_routes_require_auth(self):
        for endpoint in ['recommend','recommend/stream']:
            self.assertEqual(self.client(False).post('/api/v1/chat/'+endpoint,json={'prompt':'Tư vấn'}).status_code,401)

    def test_db_identity_and_stream_context(self):
        intent=build_profile_intent(profile(),'Tư vấn',2026)
        with patch('app.modules.graphrag.profile_context.get_full_student_profile',return_value=profile()) as read, patch('app.modules.graphrag.router.execute_query_async',new=AsyncMock(return_value=[])) as graph:
            r=self.client().post('/api/v1/chat/recommend',json={'prompt':'Tư vấn'})
            self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(read.call_args.args[1],'account-a')
            self.assertEqual(graph.call_args.args[1]['student_score'],18)
            self.assertEqual(graph.call_args.args[1]['holland_code'],'SIA')

    def test_stream_uses_profile_and_reports_missing_inputs(self):
        async def report(*args):
            yield 'data: {"token":"Tư vấn từ hồ sơ"}\n\n'
        with patch('app.modules.graphrag.profile_context.get_full_student_profile',return_value=profile()), patch('app.modules.graphrag.router.execute_query_async',new=AsyncMock(return_value=[])), patch('app.modules.graphrag.router.stream_portfolio_ai_consultation',new=report):
            response=self.client().post('/api/v1/chat/recommend/stream',json={'prompt':'Tư vấn'})
            self.assertEqual(response.status_code,200,response.text)
            self.assertIn('stored_assessment',response.text)
            self.assertIn('[DONE]',response.text)
        p=profile();p.latest_riasec=None
        with patch('app.modules.graphrag.profile_context.get_full_student_profile',return_value=p):
            response=self.client().post('/api/v1/chat/recommend/stream',json={'prompt':'Tư vấn'})
            self.assertEqual(response.status_code,422,response.text)

    def test_no_fabricated_fallback_on_graph_failure(self):
        with patch('app.modules.graphrag.profile_context.get_full_student_profile',return_value=profile()), patch('app.modules.graphrag.router.execute_query_async',new=AsyncMock(side_effect=RuntimeError('offline'))):
            for endpoint in ['recommend','recommend/stream']:
                r=self.client().post('/api/v1/chat/'+endpoint,json={'prompt':'Tư vấn'})
                self.assertEqual(r.status_code,503,r.text)

if __name__=='__main__': unittest.main()
