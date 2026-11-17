# For Your Future (for-your-future)
> Nền tảng Trắc nghiệm, Hướng nghiệp và Tư vấn Tuyển sinh Đại học Đột phá dựa trên **Deterministic GraphRAG** (Zero-Hallucination).

---

## 1. Giới thiệu & Tên dự án
* **Tên hiển thị chính thức**: **For Your Future**
* **Tên dự án & thư mục**: `for-your-future/`
* **Mã định danh hệ thống**: `for-your-future` (hoặc `for_your_future`)
* **Nguyên tắc cốt lõi**:
  - **Zero-Hallucination Policy**: Tuyệt đối không để LLM tự suy diễn hay bịa đặt điểm chuẩn, học phí hoặc chỉ tiêu ngoài đồ thị tri thức đã xác thực.
  - **Deterministic Pruning (Cắt tỉa Tất định 100%)**: Bộ lọc cứng toán học (Hard Constraint Filtering) trên Neo4j Cypher xử lý điểm chuẩn, điểm sàn đầu vào, ngân sách học phí thực tế sau bù giá (NĐ 116), thể lực (chiều cao, cận thị) và độ khớp mã Holland RIASEC.
  - **Natural Language Intent Extraction**: Bóc tách chính xác điểm số, khối thi, khu vực mong muốn, quê quán (tính điểm ưu tiên KV1, KV2, KV2-NT, KV3 theo Quy chế Tuyển sinh 2025) và ngân sách từ câu hỏi tự nhiên.

---

## 2. Kiến trúc Hệ thống (Modular Monolith)

```
for-your-future/
  ├── apps/
  │   ├── web/                     # Frontend SPA Client (Tailwind CSS, Lucide, SSE Streaming)
  │   │   └── public/
  │   │       ├── index.html       # Single Page Application Shell
  │   │       ├── app.js           # 4-Tab Profile Form, Recommend Wizard, AI Chat Drawer
  │   │       ├── admissions/2026/ # Dữ liệu đề án tuyển sinh 126 trường Đại học
  │   │       └── quiz-sources/    # Bộ 60 câu hỏi RIASEC chuẩn hóa
  │   └── api/                     # Backend Modular Monolith (FastAPI + Pydantic v2)
  │       ├── app/
  │       │   ├── core/            # Config, Security (PBKDF2/JWT), Database, ORM Models
  │       │   ├── modules/
  │       │   │   ├── auth/            # Quản lý tài khoản User & JWT Authentication
  │       │   │   ├── students/        # Hồ sơ 4 Tab (Cá nhân, Học bạ 5 HK, Tài chính, Sức khỏe)
  │       │   │   ├── assessments/     # Trắc nghiệm RIASEC & MBTI độc lập
  │       │   │   ├── universities/    # Tra cứu 126 trường đại học, ngành đào tạo
  │       │   │   ├── careers/         # 5 ngành nghề trọng điểm, kỹ năng, doanh nghiệp
  │       │   │   ├── recommendations/ # Deterministic Pruning Engine
  │       │   │   ├── consultation/    # Intent Extractor, Agentic Tool & SSE Streaming
  │       │   │   └── administration/  # Health Probes & Giám sát hệ thống
  │       │   ├── integrations/
  │       │   │   ├── neo4j/       # Async / Sync Bolt Driver & CypherQueryBuilder
  │       │   │   └── ollama/      # Ollama Client, Grounded Prompting & Fallback Generator
  │       │   └── main.py          # FastAPI Gateway & Static SPA Mounting
  ├── infrastructure/
  │   ├── docker-compose.yml       # Khởi chạy Docker trọn gói
  │   └── Dockerfile.api           # Container image cho FastAPI backend
  ├── scripts/
  │   └── start.sh                 # Script chạy nhanh môi trường development
  ├── .env.example
  └── README.md
```

---

## 3. Cấu hình Cơ sở dữ liệu Chuẩn hóa

### 3.1. CSDL Quan hệ Giao dịch (PostgreSQL - Aiven Cloud)
* **Kết nối**: `postgresql://avnadmin:***@pg-1a5f2827-thanhtiendz209-1f86.b.aivencloud.com:26350/defaultdb?sslmode=require`
* **Driver**: `psycopg2-binary` (sync pooling) và `asyncpg` (async engine).
* **Bảng dữ liệu (15 tables)**:
  - `users`: Tài khoản định danh, phân quyền role (`student`, `admin`).
  - `student_profiles`: Thông tin cá nhân, trường THPT, niên khóa.
  - `student_backgrounds`: Quê quán, thu nhập, ngân sách học phí, khu vực ưu tiên và điểm ưu tiên động Quy chế 2025.
  - `academic_profiles`: Học bạ 5 học kỳ, điểm thi tốt nghiệp THPT, chứng chỉ IELTS, SAT, điểm ĐGNL ĐHQG TP.HCM / ĐHQG HN, ĐGTD Bách khoa HN.
  - `health_profiles`: Chiều cao, cân nặng, BMI, độ cận thị 2 mắt, mù màu, giấy khám sức khỏe sơ tuyển.
  - `personality_results`: Kết quả trắc nghiệm RIASEC (6 nhóm R-I-A-S-E-C) và MBTI (lưu độc lập timestamp).
  - `universities`, `programs`, `admission_criteria`, `careers`, `chat_sessions`, `chat_messages`, `query_logs`.

### 3.2. CSDL Đồ thị Tri thức (Neo4j Graph Database)
* **Cổng kết nối**: `bolt://localhost:7687` (User: `neo4j`, Password: `***`, Database: `neo4j`).
* **Ontology Nodes & Relationships**:
  - `(h:HollandType)-[:ALIGNED_WITH]->(c:Career)`
  - `(p:Program)-[:PREPARES_FOR]->(c:Career)`
  - `(p:Program)-[:OFFERED_BY]->(u:University)`
  - `(p:Program)-[:HAS_CRITERIA]->(ad:AdmissionCriteria)-[:REQUIRES_GROUP]->(sg:SubjectGroup)`
  - `(p:Program)-[:HAS_FINANCIAL]->(fa:FinancialAspect)`
  - `(u:University)-[:LOCATED_AT]->(loc:Location)`

---

## 4. Các Tính năng Nổi bật Đã hoàn thiện

### 4.1. Bộ Bóc tách Ý định Tự nhiên (Intent & Entity Extractor)
* Phân tích câu hỏi tự nhiên như:
  > *"Tôi 25 điểm A01 ở Long An muốn học ở đại học ở HCM với kinh phí 100triệu"*
* **Trích xuất tự động**:
  - `Điểm = 25.0`
  - `Khối thi = A01`
  - `Khu vực mong muốn = TP.HCM`
  - `Quê quán = Long An` $\rightarrow$ Tự động gán `Khu vực 2 (KV2)` $\rightarrow$ Điểm ưu tiên $+0.5$ điểm.
  - `Ngân sách = 100,000,000 VND`
* Nếu học sinh đã đăng nhập, tự động lấy các trường còn thiếu từ PostgreSQL làm ngữ cảnh mặc định.
* Tự động truyền vào `CypherQueryBuilder` để truy vấn chính xác trên Neo4j Knowledge Graph:
  - **UIT** (Trường ĐH Công nghệ Thông tin - ĐHQG TP.HCM): Điểm chuẩn 25.5, Biên độ 0.0 (Target).
  - **SPK** (Trường ĐH Sư phạm Kỹ thuật TP.HCM): Điểm chuẩn 24.5, Biên độ +1.0 (Target).

### 4.2. Giao diện Hồ sơ Học sinh 4 Tab Toàn diện (`#profile`)
1. **Tab 1: Cá nhân & Quê quán**: Thông tin cơ bản, trường THPT, tỉnh thành quê quán (tự động nhận diện Khu vực ưu tiên).
2. **Tab 2: Học bạ & Điểm thi**: Điểm TB 5 học kỳ, Hạnh kiểm Lớp 12, Điểm thi tốt nghiệp THPT 6 môn (Toán, Lý, Hóa, Sinh, Văn, Anh), Chứng chỉ IELTS, Điểm thi ĐGNL (ĐHQG HCM thang 1200, ĐHQG HN thang 150).
3. **Tab 3: Bối cảnh Tài chính**: Thu nhập, ngân sách học phí hàng năm, đối tượng ưu tiên chính sách (01..07), diện hộ nghèo.
4. **Tab 4: Sức khỏe & Thể lực**: Chiều cao, cân nặng, chỉ số BMI, độ cận thị từng mắt, mù màu, giấy khám sức khỏe sơ tuyển.

### 4.3. Cắt tỉa Nguyện vọng Đa tiêu chí (`#recommend`)
* Nút bấm **"⚡ Nạp nhanh từ Hồ sơ học tập"**: Tự động điền toàn bộ điểm thi, khối thi, ngân sách và sở thích từ hồ sơ học sinh chỉ với 1 click.
* Thẻ kết quả hiển thị minh bạch 5 thông số bắt buộc:
  - **Khối thi xét tuyển** (VD: A01, A00, D01)
  - **Điểm sàn tối thiểu** (Minimum Threshold)
  - **Điểm dôi dư an toàn** (Score Margin: Safe / Target / Reach)
  - **Tiêu chí phụ khi hòa điểm** (VD: Ưu tiên môn Toán)
  - **Link Đề án Tuyển sinh chính thức**

---

## 5. Hướng dẫn Khởi chạy Ứng dụng

### 5.1. Khởi chạy Local Development (Khuyến nghị)
1. Đảm bảo dịch vụ Neo4j container đang hoạt động trên port 7687:
   ```bash
   docker start neo4j-career
   ```
2. Khởi chạy FastAPI Backend & phục vụ Web SPA:
   ```bash
   ./scripts/start.sh
   ```
3. Truy cập ứng dụng:
   - Giao diện Web: [http://localhost:8000](http://localhost:8000)
   - API Docs Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Bảng Kiểm tra Sức khỏe: [http://localhost:8000/#admin](http://localhost:8000/#admin)

### 5.2. Tài khoản Thử nghiệm Mẫu
* **Tài khoản Học sinh**:
  - Email: `student@foryourfuture.edu.vn`
  - Mật khẩu: `Student@2026`
  - Quê quán: Long An (KV2, +0.5đ), Điểm thi A01: 25.0, IELTS: 6.5, ĐGNL HCM: 850
* **Tài khoản Quản trị**:
  - Email: `admin@foryourfuture.edu.vn`
  - Mật khẩu: `Admin@2026`

