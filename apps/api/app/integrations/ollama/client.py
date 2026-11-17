"""
Ollama Client with Streaming SSE, Health Probing, and Intelligent Deterministic Fallback.
Provides uninterrupted consultation experience even when local LLM is offline or overloaded.
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from app.core.config import settings
from .prompts import build_zero_hallucination_system_prompt, sanitize_user_input

logger = logging.getLogger("foryourfuture.ollama")


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> Dict[str, Any]:
        """Kiểm tra kết nối tới Ollama Server và danh sách models có sẵn"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "base_url": self.base_url,
                        "current_model": self.model,
                        "available_models": models,
                    }
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {res.status_code}",
                    "base_url": self.base_url
                }
        except Exception as e:
            return {
                "status": "offline",
                "error": str(e),
                "base_url": self.base_url,
                "note": "Local Ollama service not running; deterministic fallback generator is active."
            }

    async def generate_fallback_stream(
        self,
        query_text: str,
        context_items: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        Fallback generator tất định: sinh bài tư vấn chuẩn mực, có trích dẫn dữ liệu thực tế
        khi Ollama server không phản hồi. Trả về format SSE chuẩn data: {"token": "..."}.
        """
        if not context_items:
            empty_msg = (
                "Chào bạn! Rất tiếc hiện tại với các tiêu chí bạn đưa ra (điểm số, ngân sách học phí hoặc tổ hợp xét tuyển), "
                "hệ thống chưa tìm thấy chương trình nào phù hợp để thỏa mãn 100% các điều kiện sàn và ngân sách.\n\n"
                "**Gợi ý điều chỉnh để mở rộng cơ hội:**\n"
                "- Cân nhắc mở rộng thêm các tỉnh/thành phố lân cận ngoài khu vực ưu tiên.\n"
                "- Tham khảo thêm các trường công lập có chính sách học bổng hoặc ngành được nhà nước hỗ trợ học phí.\n"
                "- Xem xét thêm các phương thức xét tuyển kết hợp chứng chỉ hoặc học bạ nếu điểm thi THPT đang sát ngưỡng."
            )
            for word in empty_msg.split(" "):
                yield f"data: {json.dumps({'token': word + ' '}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.015)
            yield "data: [DONE]\n\n"
            return

        top_choice = context_items[0]
        paragraphs = [
            f"Chào bạn! Cảm ơn bạn đã chia sẻ nguyện vọng. Dựa trên hồ sơ của bạn với mã sở thích nghề nghiệp **{top_choice.get('holland_code', 'RIASEC')}** và điểm xét tuyển hiện tại, tôi đã đối chiếu dữ liệu tuyển sinh thực tế và có những phân tích chiến lược sau đây:\n\n",
            "### 1. Đánh giá tổng quan năng lực & Độ an toàn điểm số\n",
            f"Với điểm xét tuyển hiện tại, bạn đang nắm giữ lợi thế rất khả quan. Cụ thể với nguyện vọng tiêu biểu **{top_choice.get('program_name')}** tại trường **{top_choice.get('university_name')}**, "
            f"bạn đang có biên độ an toàn **+{top_choice.get('score_margin', 0):.2f} điểm** (xếp loại **{top_choice.get('safety_level', 'Safe')}**). "
            "Biên độ này giúp bạn tạo được khoảng đệm an toàn vững chắc trước các biến động điểm chuẩn của mùa tuyển sinh năm nay.\n\n",
            "### 2. Phân tích chi tiết các chương trình đào tạo tối ưu\n"
        ]

        for idx, item in enumerate(context_items, 1):
            margin = item.get("score_margin", 0)
            safety = item.get("safety_level", "Safe")
            tuition = item.get("actual_tuition", 0)
            growth = item.get("job_growth_rate", 0)
            match_pct = float(item.get("holland_match_score", 1.0)) * 100
            companies = ", ".join(item.get("hiring_companies", [])) or "Các doanh nghiệp đầu ngành"
            
            p_text = (
                f"**Nguyện vọng #{idx}: {item.get('program_name')} — {item.get('university_name')}**\n"
                f"- **Mức độ an toàn điểm số**: Điểm chuẩn tham chiếu là **{item.get('benchmark_score')}**, "
                f"điểm của bạn chênh lệch **+{margin:.2f} điểm** (Đánh giá: **{safety}**).\n"
                f"- **Chi phí & Học phí**: Mức học phí thực tế là **{tuition:,.0f} VNĐ/năm**, "
                f"hoàn toàn nằm trong giới hạn ngân sách bạn mong muốn.\n"
                f"- **Cơ hội việc làm**: Chương trình chuẩn bị trực tiếp cho nghề **{item.get('career_name')}** "
                f"với tốc độ tăng trưởng nhu cầu nhân lực dự kiến **+{growth}%**. "
                f"Các đơn vị tuyển dụng tiêu biểu: {companies}.\n"
                f"- **Độ tương thích tính cách**: Đạt mức **{match_pct:.1f}%** đối với nhóm sở thích của bạn.\n\n"
            )
            paragraphs.append(p_text)

        paragraphs.append(
            "### 3. Lời khuyên hành động & Chiến lược đăng ký nguyện vọng\n"
            "- **Sắp xếp thứ tự nguyện vọng**: Hãy đặt ngành bạn thực sự yêu thích nhất lên Nguyện vọng 1, "
            "kết hợp các nguyện vọng Safe làm phương án dự phòng bảo hiểm.\n"
            "- **Chuẩn bị hồ sơ & ngoại ngữ**: Tiếp tục duy trì phong độ ôn tập và bổ sung chứng chỉ ngoại ngữ nếu có để tối đa hóa điểm ưu tiên.\n"
            "- Bạn hoàn toàn có thể tự tin với những lựa chọn trên. Hãy giữ vững tâm lý để đạt kết quả thi cử tốt nhất nhé!"
        )

        full_text = "".join(paragraphs)
        for word in full_text.split(" "):
            payload = json.dumps({"token": word + " "}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.015)

        yield "data: [DONE]\n\n"

    async def stream_consultation(
        self,
        query_text: str,
        context_items: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        Streaming hội thoại tư vấn qua SSE. Gọi Ollama nếu khả dụng, tự động fallback nếu không.
        """
        sanitized_query = sanitize_user_input(query_text)
        prompt = build_zero_hallucination_system_prompt(context_items, sanitized_query)
        ollama_url = f"{self.base_url}/api/generate"

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                req_payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.8
                    }
                }
                async with client.stream("POST", ollama_url, json=req_payload) as response:
                    if response.status_code != 200:
                        logger.warning(f"Ollama returned {response.status_code}, falling back to intelligent generator")
                        async for chunk in self.generate_fallback_stream(sanitized_query, context_items):
                            yield chunk
                        return

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                            if data.get("done", False):
                                yield "data: [DONE]\n\n"
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.info(f"Ollama request error ({e}), switching seamlessly to deterministic fallback generator.")
            async for chunk in self.generate_fallback_stream(sanitized_query, context_items):
                yield chunk

