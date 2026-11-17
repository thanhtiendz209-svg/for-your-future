# docs/PROJECT_CONTEXT.md — Ngữ cảnh Dự án For Your Future

> **Cập nhật lần cuối**: 2026-11-13 bởi Antigravity AI  
> **Mục đích**: Tài liệu này cung cấp toàn bộ ngữ cảnh cần thiết để AI agent bắt đầu làm việc ngay mà không cần hỏi lại từ đầu.

---

## 1. TỔNG QUAN DỰ ÁN

**Tên**: For Your Future  
**Mô tả**: Nền tảng trắc nghiệm, hướng nghiệp và tư vấn tuyển sinh đại học cho học sinh THPT Việt Nam.  
**Thư mục gốc**: `/home/labsit/for-your-future/`  
**URL local**: `http://localhost:8000`  
**Ngôn ngữ giao diện**: Tiếng Việt hoàn toàn.

**Nguyên tắc cốt lõi**:
- **Zero-Hallucination**: LLM không được tự bịa điểm chuẩn, học phí, chỉ tiêu.
- **Deterministic Pruning**: Lọc nguyện vọng bằng toán học cứng (Cypher query Neo4j).
- **Grounded Data**: Mọi thông tin tuyển sinh phải từ DB đã được seed từ đề án chính thức 2026.

---

## 2. KIẾN TRÚC HỆ THỐNG

```
for-your-future/
├── apps/
│   ├── web/                         # Frontend SPA
│   │   ├── public/                  # Source (sửa tại đây)
│   │   │   ├── index.html           # SPA shell, version hiện tại: v=3.5.1
│   │   │   ├── app.js               # 4972 dòng, toàn bộ UI logic
│   │   │   ├── styles.css           # Tailwind + CSS custom tokens
│   │   │   ├── logo.jpg             # Logo chính thức (tay nắm + orbit)
│   │   │   ├── data/
│   │   │   │   ├── universities.json    # 126 trường (metadata cơ bản)
│   │   │   │   └── school_details.json  # 126 trường (ngành, điểm, học phí) — 3.3MB
│   │   │   ├── personality/         # SVG animated MBTI (16 type × 2)
│   │   │   ├── illustrations/       # Hình minh họa quiz, riasec...
│   │   │   └── quiz-sources/        # Bộ 60 câu hỏi RIASEC chuẩn hóa
│   │   └── dist/                    # Build output — LUÔN sync từ public/
│   └── api/                         # Backend FastAPI
│       └── app/
│           ├── core/                # Config, DB, Security, Models
│           ├── modules/
│           │   ├── auth/            # JWT auth
│           │   ├── students/        # Hồ sơ học sinh 4 tab
│           │   ├── assessments/     # RIASEC, MBTI quiz
│           │   ├── universities/    # 126 trường API
│           │   ├── careers/         # Ngành nghề
│           │   ├── recommendations/ # Deterministic engine
│           │   ├── consultation/    # AI chat + SSE streaming
│           │   ├── graphrag/        # Neo4j + LLM grounding
│           │   └── administration/  # Health monitor
│           └── main.py
├── docs/
│   ├── PROJECT_CONTEXT.md           # (file này)
│   ├── WORK_HISTORY.md
│   ├── TODO.md
│   └── design-system.md            # Màu sắc, typography, components
├── data/
│   ├── raw/                         # Excel gốc từ người dùng
│   ├── staging/
│   └── reports/
├── scripts/                         # start.sh, seed scripts
├── infrastructure/                  # Docker compose, Dockerfile
├── AGENTS.md                        # Quy tắc cho AI agents (ĐỌC TRƯỚC)
└── README.md                        # Giới thiệu dự án
```

---

## 3. CƠ SỞ DỮ LIỆU

### 3.1 PostgreSQL — Aiven Cloud (PRIMARY)
```
Host:     pg-1a5f2827-thanhtiendz209-1f86.b.aivencloud.com
Port:     26350
Database: defaultdb
User:     avnadmin
SSL:      require
```
> ⚠️ **KHÔNG** thay đổi connection string này.

**15 bảng chính**:

| Bảng | Mô tả | Số bản ghi |
|------|-------|-----------|
| `universities` | 126 trường đại học | 126 |
| `programs` | Ngành đào tạo | ~3,482 |
| `admission_criteria` | Điểm chuẩn theo phương thức | ~14,547 |
| `users` | Tài khoản người dùng | — |
| `student_profiles` | Thông tin cá nhân | — |
| `student_backgrounds` | Tài chính, khu vực ưu tiên | — |
| `academic_profiles` | Học bạ 5 HK, điểm thi | — |
| `health_profiles` | Chiều cao, cân nặng, mắt | — |
| `personality_results` | Kết quả RIASEC + MBTI | — |
| `careers` | Ngành nghề trọng điểm | — |
| `chat_sessions` | Phiên tư vấn AI | — |
| `chat_messages` | Lịch sử chat | — |
| `query_logs` | Log truy vấn GraphRAG | — |

**Score fields trong `admission_criteria`**:
- `method`: `'Thi THPT'` | `'ĐGTD/ĐGNL'` | `'Xét tuyển kết hợp'` | `'Xét học bạ'`
- `benchmark_score`: Điểm chuẩn thực
- `score_scale`: 30.0 (THPT/học bạ) | 100.0 (ĐGTD) | 1200.0 (ĐGNL ĐHQG HCM)
- **Validation đã áp dụng**: THPT > 30 → NULL; Học bạ > 100 → NULL; Kết hợp > 1200 → NULL

### 3.2 Neo4j Graph Database (Knowledge Graph)
```
Bolt:     bolt://localhost:7687
User:     neo4j
Database: neo4j
```
**Các node types**: `HollandType`, `Career`, `Program`, `University`, `AdmissionCriteria`, `SubjectGroup`, `FinancialAspect`, `Location`

### 3.3 SQLite (Local Fallback)
```
Path: /home/labsit/for-your-future/apps/api/foryourfuture.db
```
Dùng khi không có kết nối internet đến Aiven.

---

## 4. API ENDPOINTS

**Base URL**: `http://localhost:8000`  
**Prefix**: `/api/v1`

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/v1/universities` | Danh sách 126 trường (hỗ trợ `?q=&limit=&offset=`) |
| GET | `/api/v1/universities/{uni_id}` | Chi tiết trường (programs + criteria) |
| GET | `/api/v1/admin/health` | Health check |
| POST | `/api/v1/auth/login` | Đăng nhập, trả JWT |
| POST | `/api/v1/auth/register` | Đăng ký |
| GET | `/api/v1/students/profile` | Hồ sơ học sinh (cần JWT) |
| POST | `/api/v1/students/profile` | Lưu hồ sơ |
| POST | `/api/v1/consultation/chat` | AI chat (SSE streaming) |
| GET | `/api/v1/recommendations` | Gợi ý nguyện vọng |

**Định dạng response `GET /api/v1/universities/{uni_id}`**:
```json
{
  "uni_id": "uni-001",
  "name": "Đại học Bách khoa Hà Nội (HUST)",
  "short_name": "HUST",
  "type": "Kỹ thuật",
  "location": "Hà Nội",
  "region": "Miền Bắc",
  "website": "https://hust.edu.vn/",
  "admissions_url": "https://ts.hust.edu.vn/",
  "focus_riasec": ["R","I","C"],
  "programs": [{
    "program_id": "uni-001-BF-E12",
    "major_code": "BF-E12",
    "name": "Kỹ thuật Thực phẩm (CT tiên tiến)",
    "degree_level": "Cử nhân / Kỹ sư",
    "tuition_annual": 28000000,
    "criteria": [{
      "criteria_id": "...",
      "year": 2026,
      "method": "Thi THPT",
      "group_code": "A00",
      "benchmark_score": 20.3,
      "score_scale": 30.0
    }]
  }]
}
```

---

## 5. FRONTEND SPA — app.js (4972 dòng)

### Các section chính (theo thứ tự dòng):

| Dòng | Section | Route |
|------|---------|-------|
| 15 | State & Storage | — |
| 82 | Data Initialization | — |
| 111 | Utilities (formatVND, refreshIcons...) | — |
| 157 | Router Dispatcher | — |
| 250 | **Section 0**: Authentication | `#dang-nhap`, `#dang-ky` |
| 742 | **Section 1**: Home View | `#home` |
| 1963 | **Section 2**: Quizzes & Quiz Player | `#trac-nghiem`, `#lam-trac-nghiem` |
| 1289 | RIASEC 3-Avatar Triplet Renderer | — |
| 3086 | **Section 3**: Personalities View | `#nhom-tinh-cach` |
| 3144 | **Section 4**: Careers & Universities | `#huong-nghiep` |
| 3198 | **Section 5**: Universities List | `#truong-dai-hoc` |
| 3347 | **Section 5b**: School Detail Page | `#truong-dai-hoc/uni-XXX` |
| 3712 | **Section 6**: Profile 4-Tab | `#ho-so` |
| 4076 | **Section 8**: Comparison | `#so-sanh` |
| 4243 | **Section 9**: Admin/Health | `#quan-tri` |
| 4348 | **Section 7**: About | `#gioi-thieu` |
| 4406 | Theme Init | — |
| 4454 | AI Consultation + GraphRAG | `#tu-van` |
| 4962 | Bootstrap | — |

### State object quan trọng:
```javascript
state = {
  user: null,              // JWT decoded user
  token: null,             // JWT token
  results: {               // Quiz results
    mbti: null,            // 'INTJ', 'ENFP'...
    riasec: null,          // {R:12, I:8, A:5, S:3, E:7, C:4}
    bigfive: null,
    cognitive: null,
  },
  universities: [],        // 126 trường từ universities.json
  schoolDetails: [],       // 126 trường từ school_details.json (3.3MB)
  uniFilter: { query:'', region:'Tất cả', tuition:'Tất cả' },
  schoolProgramFilter: '', // Bộ lọc trang chi tiết trường
  schoolProgramMethod: 'Tất cả',
  studentProfile: {},      // Hồ sơ học sinh 4 tab
  activeProfileTab: 'tests',
}
```

### Design System Tokens (Tailwind):
- **navy** `#0B3A62`, **azure** `#1A6DB5`, **cyan** `#2AB8C9`
- **ice** `#E8F3FB`, **mist** `#F3F8FC`, **paper** `#F6FAFD`
- **card** `#FFFFFF`, **ink** `#12304A`, **muted** `#5B7590`, **line** `#D5E4F0`
- Font: `Plus Jakarta Sans` (display), `Be Vietnam Pro` (body)

---

## 6. DỮ LIỆU NGUỒN

| File | Nội dung | Path |
|------|---------|------|
| `126_truong_va_nganh_ke_hoach_hoc_phi.xlsx` | Học phí 80/126 trường | `.user_uploaded/media_1794490637879_63cdfaa6.xlsx` |
| `126_truong_diem_2026.xlsx` | Điểm chuẩn 2026 | `.user_uploaded/media_1794490903668_fda86325.xlsx` |
| `school_details.json` | Đã extract từ 2 file trên | `apps/web/public/data/school_details.json` |
| `universities.json` | Metadata 126 trường | `apps/web/public/data/universities.json` |

**Data quality notes**:
- 80/126 trường có học phí; trường quân đội/công an có học phí = 0 (miễn phí)
- Dữ liệu điểm từ formula cell Excel → đọc bằng `openpyxl data_only=True`

---

## 7. TÀI KHOẢN THỬ NGHIỆM

| Role | Email | Mật khẩu |
|------|-------|---------|
| Student | `student@foryourfuture.edu.vn` | `Student@2026` |
| Admin | `admin@foryourfuture.edu.vn` | `Admin@2026` |

---

## 8. LỆNH THƯỜNG DÙNG

```bash
# Khởi động server
cd /home/labsit/for-your-future/apps/api
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Kiểm tra syntax app.js
node --check /home/labsit/for-your-future/apps/web/public/app.js

# Sync public → dist
cp apps/web/public/app.js apps/web/dist/app.js
cp apps/web/public/index.html apps/web/dist/index.html

# Test API
curl -s http://localhost:8000/api/v1/universities?limit=3
curl -s http://localhost:8000/api/v1/universities/uni-001

# Kiểm tra DB counts
curl -s "http://localhost:8000/api/v1/universities?limit=200" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} universities')"
```

---

## 9. LOGO & BRANDING

- **Logo file**: `/home/labsit/for-your-future/apps/web/public/logo.jpg`
- **Mô tả**: Hai bàn tay nắm nhau với vòng orbit màu xanh — biểu tượng sức mạnh tương hỗ
- **Sử dụng**: Header (40×40px), Footer (32×32px), Favicon (`/logo.jpg`)
- **Màu chủ đạo thương hiệu**: Navy `#0B3A62`

