# AGENTS.md — Hướng dẫn AI Agents làm việc trên dự án For Your Future

> **Áp dụng cho**: Antigravity AI, OpenAI Codex, và mọi AI agent làm việc trên repo này.  
> **Phiên bản**: 1.0.0 — Tạo lần đầu: 2026-11-13

---

## 🚦 QUY TẮC BẮT BUỘC TRƯỚC KHI LÀM VIỆC

### Bước 1 — Đọc ngữ cảnh (LUÔN LUÔN làm đầu tiên)
Trước khi thực hiện BẤT KỲ thay đổi nào, đọc theo thứ tự:

```
1. docs/PROJECT_CONTEXT.md   ← Kiến trúc, stack, DB, API endpoints
2. docs/WORK_HISTORY.md      ← Những gì đã làm (tránh làm lại hoặc xung đột)
3. docs/TODO.md              ← Nhiệm vụ còn tồn đọng và ưu tiên
```

### Bước 2 — Kiểm tra file lock
```bash
ls /home/labsit/for-your-future/.agent-lock/ 2>/dev/null
```
- Nếu thấy file `.lock` cho file bạn muốn sửa → **DỪNG LẠI**, báo cáo conflict.
- Nếu không có lock → tạo lock trước khi sửa (xem mục "Cơ chế Lock" bên dưới).

### Bước 3 — Kiểm tra server
```bash
curl -s http://localhost:8000/api/v1/admin/health | python3 -m json.tool
```
Nếu server không chạy:
```bash
cd /home/labsit/for-your-future/apps/api
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Bước 4 — Làm việc và ghi log
Sau khi hoàn thành nhiệm vụ, **bắt buộc** cập nhật:
- `docs/WORK_HISTORY.md` — Thêm entry mới vào đầu (prepend)
- `docs/TODO.md` — Đánh dấu done / thêm task mới nếu phát sinh

---

## 🔒 CƠ CHẾ LOCK FILE (Tránh chỉnh sửa đồng thời)

Thư mục lock: `/home/labsit/for-your-future/.agent-lock/`

### Tạo lock trước khi sửa file
```bash
mkdir -p /home/labsit/for-your-future/.agent-lock
echo "AGENT=Antigravity | TASK=... | TIME=$(date -Iseconds)" \
  > /home/labsit/for-your-future/.agent-lock/app.js.lock
```

### Xóa lock sau khi xong
```bash
rm /home/labsit/for-your-future/.agent-lock/app.js.lock
```

### Các file cần lock khi sửa
| File | Lock name |
|------|-----------|
| `apps/web/public/app.js` | `app.js.lock` |
| `apps/web/public/index.html` | `index.html.lock` |
| `apps/web/public/styles.css` | `styles.css.lock` |
| `apps/api/app/modules/*/service.py` | `api-service.lock` |
| `docs/WORK_HISTORY.md` | `work-history.lock` |
| `docs/TODO.md` | `todo.lock` |

> **Lưu ý**: Lock chỉ có tác dụng nếu cả hai AI đều tuân thủ. Đây là giao thức hợp tác, không phải mutex hệ thống.

---

## 📋 QUY TẮC CHỈNH SỬA CODE

### Frontend (app.js)
- **Luôn chạy syntax check sau khi sửa**:
  ```bash
  node --check /home/labsit/for-your-future/apps/web/public/app.js
  ```
- **Luôn sync sang dist sau khi sửa**:
  ```bash
  cp apps/web/public/app.js apps/web/dist/app.js
  cp apps/web/public/index.html apps/web/dist/index.html
  ```
- **Bump version** trong `index.html` mỗi khi deploy (`v=3.5.1` → `v=3.5.2`, v.v.)
- File dùng **LF encoding** (không phải CRLF). Dùng Python script cho thay thế nhiều dòng.

### CSS tiện ích đã được tạo sẵn (từ 2026-11-16)
- Website vẫn là SPA thuần JavaScript; không dùng Tailwind CDN để tạo CSS trong trình duyệt nữa.
- Sau khi đổi class tiện ích trong HTML, app.js hoặc JSON, chạy `node scripts/build_web_styles.cjs` từ thư mục gốc. Lệnh tạo `apps/web/public/utilities.css` và bản dist theo `apps/web/tailwind.static.cjs`.
- Giữ các thư viện có sẵn ở public/vendor và dist/vendor cùng giấy phép; không thêm lại CDN hoặc đổi phiên bản ngoài phạm vi nhiệm vụ.

### Backend (FastAPI)
- **Không thay đổi** cấu hình kết nối DB (PostgreSQL Aiven, Neo4j).
- Sau khi sửa backend, restart server và chạy health check.
- Tất cả endpoint mới phải có prefix `/api/v1/`.

### Database
- **TUYỆT ĐỐI KHÔNG** thay đổi connection string PostgreSQL Aiven.
- **TUYỆT ĐỐI KHÔNG** xóa dữ liệu production mà không backup.
- Thêm cột/bảng mới: dùng `ALTER TABLE`, không drop + recreate.

---

## 🤝 PHÂN CÔNG GIỮA HAI AI

| Nhiệm vụ | Ưu tiên AI | Ghi chú |
|----------|-----------|---------|
| Frontend SPA (app.js, index.html, styles.css) | Antigravity | Có context đầy đủ từ session trước |
| Backend FastAPI (routers, services, schemas) | Cả hai | Phối hợp qua docs/ |
| Database migrations | Antigravity | Đã có seed scripts |
| Data analysis / extraction | Codex | Phù hợp với tác vụ batch |
| Viết test / scripts | Cả hai | |
| Cập nhật docs/ | Cả hai | Dùng lock khi ghi |

---

## 📝 MẪU CẬP NHẬT WORK_HISTORY

Khi hoàn thành task, thêm entry vào **đầu** `docs/WORK_HISTORY.md`:

```markdown
## [DATE] [AI_NAME] — [Mô tả ngắn]

**Agent**: Antigravity / Codex  
**Thời gian**: YYYY-MM-DD HH:MM (GMT+7)  
**Files đã thay đổi**:
- `path/to/file` — Mô tả thay đổi

**Kết quả**:
- ✅ Điều đã hoàn thành

**Lưu ý cho AI tiếp theo**:
- Điểm cần chú ý
```

---

## ⚠️ NHỮNG ĐIỀU TUYỆT ĐỐI KHÔNG LÀM

1. **Không** xóa hoặc overwrite `AGENTS.md`, `docs/PROJECT_CONTEXT.md` mà không đọc trước.
2. **Không** commit thông tin bí mật (password, API key, connection string) vào docs.
3. **Không** thay đổi schema PostgreSQL Aiven hoặc Neo4j mà không ghi vào WORK_HISTORY trước.
4. **Không** sửa `app.js` mà không chạy `node --check` sau đó.
5. **Không** deploy lên dist nếu syntax check thất bại.
6. **Không** tự suy đoán điểm chuẩn, học phí — dữ liệu phải từ DB hoặc file Excel gốc.

