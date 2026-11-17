# CODEX_PROMPT.md — Prompt khởi động cho Codex / AI Agent mới

> **Copy toàn bộ file này và paste vào đầu cuộc hội thoại với Codex.**  
> Cập nhật: 2026-11-13 bởi Antigravity AI

---

## 🧠 BỐI CẢNH DỰ ÁN (ĐỌC KỸ TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ)

Bạn là AI engineer đang tiếp tục phát triển dự án **For Your Future** — nền tảng tư vấn hướng nghiệp và tuyển sinh đại học cho học sinh THPT Việt Nam. Dự án đã được xây dựng qua nhiều session, bạn đang tiếp nối công việc.

**Thư mục gốc**: `/home/labsit/for-your-future/`  
**URL ứng dụng**: `http://localhost:8000`  
**Ngôn ngữ giao diện**: Tiếng Việt hoàn toàn.

---

## 📖 NGUỒN GỐC DỰ ÁN

Dự án được tạo ra bằng cách **hợp nhất hai codebase**:

### 1. Trachngiemtinhcach_repo (Frontend gốc)
Nền tảng trắc nghiệm tính cách & hướng nghiệp với:
- React 19 + TypeScript + Vite + TailwindCSS v4
- TanStack Router (file-based routing)
- **126 trường đại học** với 7.868 chương trình, 17.825 bản ghi tuyển sinh
- Bài trắc nghiệm: **RIASEC** (60 câu, 120 tổ hợp mã 3 ký tự), **MBTI** (16 loại), **Big Five**
- Logic thuật toán `careerMatch` = kết hợp điểm RIASEC + điểm cộng MBTI

### 2. GraphRAG Backend (Backend gốc)
Hệ thống tư vấn dựa trên **Deterministic GraphRAG**:
- FastAPI + PostgreSQL (Aiven) + Neo4j (Local Docker) + Ollama (LLM local)
- **Nguyên tắc QUAN TRỌNG NHẤT**: LLM **KHÔNG** sinh Cypher. LLM chỉ làm 2 việc:
  1. Trích xuất thông tin từ câu hỏi tự nhiên → JSON (Intent Extraction)
  2. Viết báo cáo tư vấn từ JSON kết quả (Grounded Report)
- Lọc trường/ngành = **Cypher Pruning tất định** trên Neo4j (100% toán học, không xác suất)

### Kết quả hợp nhất hiện tại
Frontend React đã được **port thành SPA thuần JavaScript** (không build tool), phục vụ bởi FastAPI. Tech stack hiện tại:
- **Frontend**: Vanilla JS SPA (`app.js` 4972 dòng) + TailwindCSS CDN + Lucide Icons
- **Backend**: FastAPI (Python) + SQLAlchemy async
- **DB chính**: PostgreSQL Aiven cloud
- **DB đồ thị**: Neo4j Docker local (bolt://localhost:7687)
- **LLM**: Ollama local (Llama 3.1 8B / Qwen 2.5 7B)

---

## 🏗️ KIẾN TRÚC HIỆN TẠI

```
for-your-future/
├── apps/
│   ├── web/
│   │   ├── public/              ← SOURCE (sửa tại đây)
│   │   │   ├── index.html       ← SPA shell (version hiện tại: v=3.5.1)
│   │   │   ├── app.js           ← 4972 dòng, toàn bộ UI logic
│   │   │   ├── styles.css       ← CSS tokens + Tailwind overrides
│   │   │   ├── logo.jpg         ← Logo chính thức (tay nắm + orbit xanh)
│   │   │   ├── data/
│   │   │   │   ├── universities.json    ← 126 trường (metadata)
│   │   │   │   └── school_details.json  ← 126 trường (ngành+điểm+học phí, 3.3MB)
│   │   │   ├── personality/     ← 16 × MBTI_XXXX_animated.svg
│   │   │   └── quiz-sources/    ← 60 câu hỏi RIASEC JSON
│   │   └── dist/                ← Build output (LUÔN sync từ public/ sau khi sửa)
│   └── api/
│       └── app/
│           ├── core/            ← Config, DB engines, Security, ORM Models
│           ├── modules/
│           │   ├── auth/            ← JWT (python-jose + passlib bcrypt)
│           │   ├── students/        ← Hồ sơ học sinh 4 tab
│           │   ├── assessments/     ← RIASEC + MBTI quiz results
│           │   ├── universities/    ← 126 trường API
│           │   ├── careers/         ← Ngành nghề
│           │   ├── recommendations/ ← Deterministic Pruning Engine
│           │   ├── consultation/    ← Intent Extractor + SSE Streaming
│           │   ├── graphrag/        ← Neo4j queries + LLM grounding
│           │   │   ├── llm_service.py    ← OllamaClient (PHẢI dùng cái này)
│           │   │   ├── query_builder.py  ← CypherQueryBuilder
│           │   │   └── recommender.py    ← Deterministic Pruning Engine
│           │   └── administration/  ← Health probes
│           └── main.py          ← FastAPI gateway + static SPA mount
├── docs/
│   ├── PROJECT_CONTEXT.md   ← Đọc file này để hiểu chi tiết hơn
│   ├── WORK_HISTORY.md      ← Lịch sử công việc đã làm
│   ├── TODO.md              ← Việc cần làm
│   └── design-system.md    ← Màu sắc, typography
├── scripts/
│   ├── log_work.py          ← Script ghi lịch sử sau khi xong việc
│   └── lock.py              ← Script quản lý lock file
├── .agent-lock/             ← Thư mục lock (tránh edit đồng thời)
└── AGENTS.md                ← Quy tắc bắt buộc cho AI agents
```

---

## 🗄️ CƠ SỞ DỮ LIỆU

### PostgreSQL — Aiven Cloud (PRIMARY, ĐANG DÙNG)
```
postgresql://avnadmin:***@pg-1a5f2827-thanhtiendz209-1f86.b.aivencloud.com:26350/defaultdb?sslmode=require
```
> ⚠️ KHÔNG thay đổi connection string này (mật khẩu thật được bảo mật trong .env).

**Dữ liệu đã seed**:
- 126 universities ✅
- ~3,482 programs ✅  
- ~14,547 admission_criteria rows ✅

**15 bảng**: `users`, `student_profiles`, `student_backgrounds`, `academic_profiles`, `health_profiles`, `personality_results`, `universities`, `programs`, `admission_criteria`, `careers`, `chat_sessions`, `chat_messages`, `query_logs`

**Score fields trong `admission_criteria`**:
- `method`: `'Thi THPT'` | `'ĐGTD/ĐGNL'` | `'Xét tuyển kết hợp'` | `'Xét học bạ'`
- `score_scale`: 30.0 (THPT/học bạ) | 100.0 (ĐGTD) | 1200.0 (ĐGNL ĐHQG HCM)
- **Data validation**: THPT > 30 → NULL; Học bạ > 100 → NULL; Kết hợp > 1200 → NULL

### Neo4j — Knowledge Graph (Local Docker)
```
bolt://localhost:7687  |  user: neo4j  |  db: neo4j
```

**Ontology**:
```
(HollandType)-[:ALIGNED_WITH {weight}]->(Career)
(Program)-[:PREPARES_FOR]->(Career)
(Program)-[:OFFERED_BY]->(University)
(Program)-[:HAS_CRITERIA]->(AdmissionCriteria)-[:REQUIRES_GROUP]->(SubjectGroup)
(Program)-[:HAS_FINANCIAL]->(FinancialAspect)
(University)-[:LOCATED_AT]->(Location)
(Career)-[:REQUIRES]->(Skill|ProfessionalCert)
```

**Deterministic Pruning logic** (trong `query_builder.py`):
```cypher
// Lọc theo điểm (KHÔNG dùng LLM để sinh query này)
ad.benchmark_score <= (student_score + bonus_points)   // Đạt điểm chuẩn
AND (student_score + bonus_points) >= ad.minimum_threshold  // Đạt điểm sàn
AND fa.effective_annual_cost <= max_annual_budget       // Trong ngân sách
AND (height constraint nếu có)                          // Thể lực
AND holland_code IN focus_riasec                        // Phù hợp sở thích
```

**Safety levels**:
- `Safe`: Dôi dư ≥ 1.5 điểm
- `Target`: Dôi dư 0.0 → 1.5 điểm
- `Reach`: Điểm sát nút

### SQLite — Local Fallback
`/home/labsit/for-your-future/apps/api/foryourfuture.db`

---

## 🌐 API ENDPOINTS

**Base**: `http://localhost:8000/api/v1`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/universities` | 126 trường (`?q=&limit=&offset=`) |
| GET | `/universities/{uni_id}` | Chi tiết trường + programs + criteria |
| POST | `/auth/login` | JWT login |
| POST | `/auth/register` | Đăng ký |
| GET | `/students/profile` | Hồ sơ học sinh (cần JWT) |
| POST | `/students/profile` | Lưu hồ sơ |
| POST | `/consult/stream` | AI chat SSE streaming |
| POST | `/recommendations` | Gợi ý nguyện vọng |
| GET | `/admin/health` | Health check |

**Response `GET /universities/{uni_id}`** (rút gọn):
```json
{
  "uni_id": "uni-001",
  "name": "Đại học Bách khoa Hà Nội (HUST)",
  "short_name": "HUST",
  "focus_riasec": ["R","I","C"],
  "programs": [{
    "major_code": "BF-E12",
    "name": "Kỹ thuật Thực phẩm (CT tiên tiến)",
    "tuition_annual": 28000000,
    "criteria": [{
      "method": "Thi THPT",
      "group_code": "A00",
      "benchmark_score": 20.3,
      "score_scale": 30.0
    }]
  }]
}
```

---

## 🖥️ FRONTEND SPA — app.js (4972 dòng)

**Các route chính**:
```
#home              → Trang chủ (hero, quiz picker, career preview)
#trac-nghiem       → Danh sách bài trắc nghiệm
#lam-trac-nghiem   → Quiz player (RIASEC 60 câu / MBTI / Big Five)
#nhom-tinh-cach    → 16 nhóm MBTI + 120 tổ hợp RIASEC
#huong-nghiep      → Ngành nghề & Trường đại học
#truong-dai-hoc    → Danh sách 126 trường
#truong-dai-hoc/uni-XXX  → Trang chi tiết trường (API-first + fallback JSON)
#ho-so             → Hồ sơ học sinh 4 tab
#so-sanh           → So sánh trường (skeleton, chưa đầy đủ)
#tu-van            → AI chat + GraphRAG strategic portfolio
#dang-nhap         → Đăng nhập JWT
#dang-ky           → Đăng ký
#quan-tri          → Admin + Health monitor
```

**State quan trọng**:
```javascript
state.user          // JWT decoded user
state.token         // JWT token string
state.results.mbti  // 'INTJ', 'ENFP'...
state.results.riasec // {R:12, I:8, A:5, S:3, E:7, C:4}
state.universities  // 126 trường từ universities.json
state.schoolDetails // 126 trường từ school_details.json (3.3MB)
state.studentProfile // Hồ sơ học sinh 4 tab
```

**Design system tokens** (dùng Tailwind classes):
- `text-navy` `bg-navy` → #0B3A62 (màu chính)
- `text-azure` `bg-azure` → #1A6DB5 (màu nhấn 1)
- `text-cyan` `bg-cyan` → #2AB8C9 (màu nhấn 2)
- `bg-ice` → #E8F3FB, `bg-mist` → #F3F8FC, `bg-paper` → #F6FAFD
- `text-ink` → #12304A, `text-muted` → #5B7590, `border-line` → #D5E4F0
- Font: `Plus Jakarta Sans` (display/heading), `Be Vietnam Pro` (body)
- Rounded: `rounded-[24px]` (card lớn), `rounded-[14px]` (chip/badge)

---

## 🤖 LLM SERVICE — QUAN TRỌNG

**File**: `apps/api/app/modules/graphrag/llm_service.py`

Khi cần gọi LLM, **BẮT BUỘC dùng file này**, không tự tạo OllamaClient mới.

```python
from app.modules.graphrag.llm_service import OllamaClient

client = OllamaClient()
# Stream generate
async for chunk in client.stream_generate(prompt="...", model="llama3.1:8b"):
    yield chunk

# Fallback: nếu Ollama down → tự động sinh từ JSON context
```

**Guardrails bắt buộc**:
- Blacklist từ khóa nhạy cảm (chính trị, tôn giáo, bạo lực)
- Filter prompt injection ("ignore previous", "system:", v.v.)
- LLM chỉ được viết báo cáo từ JSON context đã có — KHÔNG được tự bịa số liệu

---

## 📏 QUY TẮC BẮT BUỘC

### Trước khi làm việc
```bash
# 1. Kiểm tra lock
python3 scripts/lock.py status

# 2. Lấy lock nếu sửa file quan trọng
python3 scripts/lock.py acquire app.js --agent Codex --task "Mô tả task"

# 3. Kiểm tra server
curl -s http://localhost:8000/api/v1/admin/health
```

### Khi sửa Frontend
```bash
# Luôn kiểm tra syntax sau khi sửa app.js
node --check /home/labsit/for-your-future/apps/web/public/app.js

# Luôn sync sang dist
cp apps/web/public/app.js apps/web/dist/app.js
cp apps/web/public/index.html apps/web/dist/index.html

# Bump version trong index.html (v=3.5.1 → v=3.5.2...)
```

### Sau khi hoàn thành
```bash
# Release lock
python3 scripts/lock.py release app.js

# Ghi lịch sử công việc
python3 scripts/log_work.py \
  --agent "Codex" \
  --task "Mô tả ngắn gọn" \
  --files "app.js:Thay đổi X" \
  --results "✅ Điều đã làm" \
  --notes "Lưu ý cho AI tiếp theo"
```

### TUYỆT ĐỐI KHÔNG
- ❌ Thay đổi connection string PostgreSQL Aiven
- ❌ Xóa dữ liệu production
- ❌ Dùng LLM để sinh Cypher query
- ❌ Để LLM tự bịa điểm chuẩn, học phí, chỉ tiêu
- ❌ Sửa app.js mà không chạy `node --check` sau đó
- ❌ Deploy lên dist nếu syntax check thất bại
- ❌ Tạo OllamaClient mới thay vì dùng `llm_service.py`

---

## 🚀 KHỞI ĐỘNG SERVER

```bash
cd /home/labsit/for-your-future/apps/api
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> Lưu ý: Port binding cần quyền network thật — trong môi trường sandbox cần bypass.

**Tài khoản test**:
- Student: `student@foryourfuture.edu.vn` / `Student@2026`
- Admin: `admin@foryourfuture.edu.vn` / `Admin@2026`

---

## 📋 VIỆC CẦN LÀM (xem chi tiết trong docs/TODO.md)

### Priority 1 — Cần làm ngay
1. Verify trang chi tiết trường `#truong-dai-hoc/uni-001` hoạt động end-to-end
2. Fix filter/search trong bảng ngành (sau khi refactor grouped rows)
3. Fix renderUniversities search realtime

### Priority 2 — Quan trọng
4. Trang so sánh trường `#so-sanh` (skeleton đã có)
5. Hiển thị RIASEC match % trong trang chi tiết trường
6. Nút "Thêm vào yêu thích" → localStorage

### Priority 3 — Nice to have
7. Admin panel edit dữ liệu trường trực tiếp
8. Export PDF kết quả trắc nghiệm + gợi ý trường
9. Search toàn cục (trường + ngành + tổ hợp)

---

## 📚 TÀI LIỆU THÊM

Đọc thêm nếu cần:
- `docs/PROJECT_CONTEXT.md` — Chi tiết đầy đủ về kiến trúc
- `docs/WORK_HISTORY.md` — Lịch sử công việc theo thời gian
- `docs/design-system.md` — Hệ thống thiết kế đầy đủ
- `AGENTS.md` — Quy tắc cho AI agents

---

*Prompt này được tổng hợp bởi Antigravity AI từ toàn bộ lịch sử hội thoại và tài liệu thiết kế gốc của dự án.*

