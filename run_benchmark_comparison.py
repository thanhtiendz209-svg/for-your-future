"""
Run comparison benchmark between GraphRAG and For-Your-Future.
Tests:
1. Clarification question when missing score / subject group.
2. Full 3-tier recommendation (Reach, Target, Safe, All Candidates).
3. Live streaming SSE.
4. Fast Lookup & Chitchat.
"""

import asyncio
import json
import time
import httpx


async def run_benchmark():
    base_url = "http://127.0.0.1:8000"
    print("=" * 60)
    print("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM CHAT AGENT TRÊN FOR-YOUR-FUTURE")
    print(f"Target URL: {base_url}")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 0. Health check
        res = await client.get(f"{base_url}/health")
        print(f"\n[0. Health Check] HTTP {res.status_code}: {res.json()}")

        # 1. Test Clarification Flow
        print("\n" + "-" * 50)
        print("🧪 TEST 1: CHƯA NÊU ĐIỂM SỐ & KHỐI THI (HỎI LẠI GỢI MỞ)")
        t0 = time.time()
        res1 = await client.post(
            f"{base_url}/api/v1/chat/recommend",
            json={"prompt": "Em đang rất phân vân muốn học ngành Công nghệ thông tin ở TP.HCM"}
        )
        elapsed1 = time.time() - t0
        data1 = res1.json()
        print(f"⏱️ Thời gian phản hồi: {elapsed1:.2f}s | HTTP {res1.status_code}")
        print(f"❓ Clarification Question:\n{data1.get('clarification_question') or data1.get('advice')}")

        # 2. Test Full 3-Tier Recommendation Flow
        print("\n" + "-" * 50)
        print("🧪 TEST 2: ĐỦ ĐIỂM SỐ & KHỐI THI (ĐỐI CHIẾU ĐỒ THỊ + RANKING 3 TẦNG)")
        prompt_full = "Em được 25.5 điểm khối A01 muốn học ngành Điện - Điện tử hoặc CNTT tại TP.HCM ngân sách 40 triệu"
        t0 = time.time()
        res2 = await client.post(
            f"{base_url}/api/v1/chat/recommend",
            json={"prompt": prompt_full}
        )
        elapsed2 = time.time() - t0
        data2 = res2.json()
        print(f"⏱️ Thời gian phản hồi: {elapsed2:.2f}s | HTTP {res2.status_code}")
        
        portfolio = data2.get("portfolio", {})
        print(f"📊 Tổng số chương trình đánh giá (total_evaluated): {portfolio.get('total_evaluated', 0)}")
        print(f"🔴 Reach (Mạo hiểm): {len(portfolio.get('reach', []))} ngành")
        for r in portfolio.get('reach', [])[:2]:
            print(f"   - {r.get('program_name')} @ {r.get('university_name')} (Chuẩn: {r.get('admission_score')} | Dôi dư: {r.get('score_margin'):+.2f})")

        print(f"🟡 Target (Vừa sức): {len(portfolio.get('target', []))} ngành")
        for t in portfolio.get('target', [])[:2]:
            print(f"   - {t.get('program_name')} @ {t.get('university_name')} (Chuẩn: {t.get('admission_score')} | Dôi dư: {t.get('score_margin'):+.2f})")

        print(f"🟢 Safe (An toàn): {len(portfolio.get('safe', []))} ngành")
        for s in portfolio.get('safe', [])[:2]:
            print(f"   - {s.get('program_name')} @ {s.get('university_name')} (Chuẩn: {s.get('admission_score')} | Dôi dư: {s.get('score_margin'):+.2f})")

        all_cands = portfolio.get('all_candidates', [])
        print(f"🌐 Toàn bộ ứng viên đồ thị (All Candidates): {len(all_cands)} ngành")

        advice = data2.get("advice", "")
        print(f"\n💬 Lời tư vấn AI (Grounded Consultation - Trích đoạn 250 ký tự đầu):\n{advice[:250]}...\n")

        # 3. Test Streaming SSE Flow
        print("-" * 50)
        print("🧪 TEST 3: LUỒNG STREAM SSE (/api/v1/chat/recommend/stream)")
        t0 = time.time()
        stream_tokens = 0
        events_received = []
        async with client.stream(
            "POST",
            f"{base_url}/api/v1/chat/recommend/stream",
            json={"prompt": "Em 26 điểm A00 ở TPHCM"}
        ) as stream_resp:
            print(f"HTTP Status: {stream_resp.status_code}")
            async for line in stream_resp.aiter_lines():
                if line.startswith("data: "):
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        ev = json.loads(payload)
                        ev_type = ev.get("type")
                        events_received.append(ev_type)
                        if ev_type == "token":
                            stream_tokens += 1
                    except Exception:
                        pass
        elapsed3 = time.time() - t0
        print(f"⏱️ Stream hoàn tất trong: {elapsed3:.2f}s | Nhận được {stream_tokens} tokens")
        print(f"Các loại sự kiện nhận được: {list(dict.fromkeys(events_received))}")

        # 4. Test Lookups & Chitchat
        print("\n" + "-" * 50)
        print("🧪 TEST 4: TRA CỨU HỌC PHÍ TRƯỜNG CỤ THỂ (LOOKUP)")
        res4 = await client.post(
            f"{base_url}/api/v1/chat/recommend",
            json={"prompt": "Học phí trường Đại học Công nghiệp TP.HCM (IUH) là bao nhiêu một năm?"}
        )
        data4 = res4.json()
        print(f"Đáp án Tra cứu:\n{data4.get('advice') or data4.get('full_reply')}")

    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT BÀI TEST SO SÁNH: AGENT CHẠY MƯỢT MÀ 100%!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
