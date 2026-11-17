# docs/TODO.md — Danh sách Việc cần làm

> **Cập nhật lần cuối**: 2026-11-13 bởi Antigravity AI  
> **Quy tắc**: Khi hoàn thành task → đổi `[ ]` thành `[x]` và ghi ngày + tên AI.

---

## 🔴 PRIORITY 1 — Cần làm ngay

- [x] Khắc phục GitHub Push Protection: loại bỏ mật khẩu Aiven thật khỏi .env.example, docs/CODEX_PROMPT.md, docker-compose.yml và config.py; chuẩn hóa .gitignore; amend commit an toàn — 2026-11-18 Antigravity.

- [x] Cập nhật khóa Gemini và cấu hình Neo4j Aura theo yêu cầu, thống nhất đọc .env; kiểm tra dịch vụ thành công và khởi động lại web cổng 8000. Hủy việc đưa mã lên GitHub theo chỉ dẫn — 2026-11-17 Codex.

- [x] Tối ưu hiệu năng desktop/mobile: CSS tạo sẵn, thư viện nội bộ, tải dữ liệu theo trang, cache lựa chọn/icon và tạm nghỉ ảnh động ngoài viewport; giữ cấu trúc/tính năng/phong cách — 2026-11-16 Codex.

- [x] Thay minh họa 4 bài test bằng SVG động từ Drive, đúng loại/tỷ lệ, lazy/async và có bản đứng yên cho reduced-motion — 2026-11-16 Codex.

- [x] Bỏ chữ viết tắt đồng sáng lập; đưa hai khung tên độc lập vào vùng trống ảnh, thêm ảnh tự nổi nhẹ, hỗ trợ mobile/theme/reduced-motion — 2026-11-16 Codex.

- [x] Nâng cấp thẻ Đồng sáng lập: nhãn/viền xanh, hai hàng tên có avatar chữ, float/shine/hover nhẹ, responsive và reduced-motion — 2026-11-16 Codex.

- [x] Thay ảnh hero bằng ảnh Drive và nhãn hai đồng sáng lập; thiết kế caption, glow/hover nhẹ, hỗ trợ điện thoại, sáng/tối và reduced-motion — 2026-11-16 Codex.

- [x] Tạo view chỉ đọc `public."dữ liệu người dùng"` trên Aiven hiện tại để tổng hợp hồ sơ và kết quả bốn bài test; giữ nguyên website/AI/dữ liệu nguồn — 2026-11-16 Codex.

- [x] Hoàn tác riêng phần nối kết quả bốn bài test vào AI theo yêu cầu; giữ nguyên giao diện đã chốt và dữ liệu người dùng — 2026-11-16 Codex.

- [x] Tối ưu UX điện thoại (menu, vùng chạm, chữ/form, modal, quiz, beacon AI) và dựng bộ lọc/SSE nhẹ hơn; giữ cấu trúc/tính năng/phong cách. Người dùng đã chốt bản này và yêu cầu bỏ backup/công cụ khôi phục — 2026-11-15 Codex.

- [x] AI mở chat mới mặc định; khôi phục đúng hội thoại nếu quay lại trong 5 phút sau khi rời; hết hạn mở mới và giữ lịch sử — 2026-11-15 Codex.

- [x] Theo đính chính: khôi phục chiều dài cũ, chỉ giảm CHIỀU CAO để thanh ngành mỏng hơn — 2026-11-15 Codex.

- [x] Khôi phục khung kết quả như cũ, chỉ thu riêng thanh chứa tên ngành; bảng chi tiết vẫn rộng — 2026-11-15 Codex.

- [x] Thu gọn chiều rộng thanh ngành, căn giữa và giữ giao diện điện thoại dễ đọc — 2026-11-15 Codex.

- [x] Làm rõ phân cấp tên ngành và thụt thông tin số trường/chương trình bên dưới — 2026-11-15 Codex.

- [x] Thiết kế giao diện AI thoáng theo ảnh tham khảo: lời chào/ô nhập giữa, chat dễ đọc, lịch sử đóng mặc định, responsive sáng/tối — 2026-11-15 Codex.

- [x] Thay ba mô tả điểm mạnh, sở thích, định hướng nghề nghiệp trên trang chủ theo câu người dùng cung cấp — 2026-11-15 Codex.

- [x] Bỏ emoji màu trong chi tiết tính cách, giữ icon nét vẽ — 2026-11-15 Codex.

- [x] Bỏ dòng Xem chi tiết dưới nhóm MBTI/RIASEC, giữ thao tác mở thông tin — 2026-11-15 Codex.

- [x] Chữ gallery tính cách không khung, bỏ tên lặp; tối ưu cache JSON, ảnh lazy/async và hiệu ứng nhẹ, giữ cấu trúc ứng dụng — 2026-11-15 Codex.

- [x] Mở rộng minh họa MBTI/RIASEC nhô khỏi thẻ, giữ nguyên ảnh cũ; responsive sáng/tối — 2026-11-15 Codex.

- [x] Giới thiệu đủ bốn bài, ưu tiên RIASEC và Đánh giá năng lực nhận thức — 2026-11-15 Codex.

- [x] **Bỏ mã ngành khỏi tiêu đề khối, chỉ giữ tên ngành** — _2026-11-15 Codex_.

- [x] **Khối ngành bo tròn giống ảnh mẫu, có hiệu ứng di chuột** — _2026-11-15 Codex_: mã và tên cùng dòng, tam giác mở/đóng, nâng/bóng nhẹ khi hover; kiểm tra sáng/tối, điện thoại và reduced-motion.

- [x] **Gom kết quả tra cứu thành khối ngành đóng/mở** — _2026-11-15 Codex_: mỗi ngành một khối, nhấn xem điểm và học phí theo trường; phân trang, tìm không dấu, hỗ trợ điện thoại và bàn phím.

- [ ] **Verify trang chi tiết trường hoạt động end-to-end**
  - Truy cập `http://localhost:8000/#truong-dai-hoc/uni-001` và kiểm tra:
    - Loading spinner hiển thị
    - API `/api/v1/universities/uni-001` được gọi
    - Bảng ngành 8 cột hiển thị đúng (THPT, ĐGTD, Kết hợp, Học bạ, Học phí)
    - Score range cards hiển thị
  - _Assigned_: AI tiếp theo khi có browser access

- [ ] **Kiểm tra và fix filter/search trong bảng ngành**
  - `renderSchoolProgramRows` đã được refactor → cần verify search theo tên ngành
  - Verify filter "Tiêu chuẩn" vs "CT tiên tiến" hoạt động đúng
  - _Note_: Sau refactor grouped logic, `methodFilter` cần map lại từ `p.type`

- [x] **Fix renderUniversities search realtime** — _2026-11-13 Codex_ 
  - Đã cập nhật riêng grid/count khi gõ, giữ focus và không nhân đôi panel/listeners; kiểm thử Chrome đạt.
  - _File_: `app.js` line 3314–3340

---

## 🟡 PRIORITY 2 — Quan trọng nhưng không khẩn cấp

- [ ] Bổ sung liên kết nghề/tổ hợp có nguồn cho các chương trình mới sau import workbook; chỉ 839/3478 chương trình giữ được context graph khớp chính xác. Không suy đoán từ tên gần giống.

- [ ] Đồng bộ nút lưu trong trang hồ sơ cũ `#ho-so` qua API như wizard mới; bổ sung phương thức ĐGNL/học bạ và quy tắc điểm ưu tiên cho luồng tư vấn.

- [ ] **Thêm trang so sánh trường theo ngành** (`#so-sanh`)
  - Cho phép chọn 2–3 trường để so sánh điểm chuẩn & học phí side-by-side
  - Khung sườn renderComparison đã có tại app.js line 4076
  - _Complexity_: Medium

- [ ] **Hiển thị RIASEC match % trong trang chi tiết trường**
  - `universities` đã có `focus_riasec: ["R","I","C"]`
  - Nếu user đã làm quiz → hiển thị badge "Phù hợp XX% với Holland code của bạn"
  - _File_: `renderSchoolDetailPage` trong app.js

- [ ] **Thêm nút "Thêm vào yêu thích"** trong trang chi tiết trường
  - Lưu vào `state.favorites[]` → localStorage
  - Hiển thị danh sách yêu thích trong `#ho-so` tab

- [ ] **Cải thiện UX của trang danh sách 126 trường**
  - Thêm filter theo loại trường (Kỹ thuật, Kinh tế, Y dược...)
  - Thêm sort (theo điểm, theo học phí)
  - Thêm chip filter cho điểm chuẩn THPT (< 20, 20–24, 24–27, > 27)

- [ ] **Thêm Học bạ filter vào trang chi tiết trường**
  - Dropdown "Phương thức xét tuyển" hiện chỉ có "Tiêu chuẩn" vs "CT tiên tiến"
  - Cần thêm: "Chỉ THPT", "Chỉ ĐGTD", "Chỉ Học bạ", "Chỉ Kết hợp"
  - _File_: `renderSchoolDetailPage` select#sd-method-filter + `renderSchoolProgramRows`

---

## 🟢 PRIORITY 3 — Nice to have

- [ ] **Admin panel để edit dữ liệu trường trực tiếp**
  - Endpoint `/api/v1/admin/universities/{uni_id}` (PATCH)
  - Form UI trong `#quan-tri` tab
  - Giúp cập nhật điểm chuẩn khi có thông tin mới

- [ ] **Export PDF báo cáo kết quả trắc nghiệm + gợi ý trường**
  - Dùng `window.print()` với CSS print media query
  - Hoặc dùng jsPDF (CDN)

- [ ] **Thêm bản đồ phân bổ trường** theo tỉnh/thành
  - SVG map của Việt Nam với dot cho mỗi trường
  - Click vào tỉnh → filter trường theo vị trí

- [ ] **Search toàn cục** (trường + ngành + tổ hợp)
  - Hộp search ở header → kết quả gộp trường + ngành

- [ ] **Trang landing giới thiệu chi tiết từng ngành nghề**  
  - Hiện có `#huong-nghiep` nhưng còn sơ sài
  - Thêm: mức lương, kỹ năng cần có, trường đào tạo tốt nhất

---

## ✅ ĐÃ HOÀN THÀNH

- [x] **Gộp tên ngành trùng, lọc đúng ngành và thêm bảng tra cứu ngành/điểm/học phí liên trường qua CTA nổi bật trong Bộ lọc** — _2026-11-15 Codex_

- [x] Đổi nút trang chủ thành **Khám phá nhóm tính cách** — _2026-11-15 Codex_

- [x] **Giới thiệu đủ bốn bài trắc nghiệm, bỏ “không phải hộp nghề”, đổi menu thành Bộ lọc** — _2026-11-15 Codex_

- [x] **Mở rộng vùng chat, gọn composer và ngăn lịch sử đóng/mở trên desktop/mobile**, luôn đóng lịch sử mặc định theo yêu cầu mới — _2026-11-15 Codex_

- [x] **Đổi trang tư vấn thành chat có lịch sử theo tài khoản**, streaming, câu hỏi tiếp nối, chọn lại cuộc trò chuyện, UI desktop/mobile — _2026-11-15 Codex_

- [x] **Hiệu ứng chuyển động nhẹ cho thẻ/nút/menu và mở ngành**, hỗ trợ chuột, cảm ứng và reduced-motion — _2026-11-14 Codex_

- [x] **Highlight hành động thẻ trường theo ảnh mẫu**, nút chính navy, nút Trang trường có viền và liên kết tuyển sinh — _2026-11-14 Codex_

- [x] **Khôi phục giao diện trước lần thêm highlight nền sáng**, theo yêu cầu người dùng; giữ dữ liệu và chức năng — _2026-11-14 Codex_

- [x] **Thay dữ liệu bằng Điểm và học phí.xlsx cập nhật 14/11; thiết kế lại trang trường**, tách phương thức/thang điểm, sync PostgreSQL và Neo4j — _2026-11-14 Codex_

- [x] **Bộ lọc trường theo mẫu, ngành/mã ngành, tỉnh mới/cũ và tìm không dấu**, kiểm tra desktop/mobile light/dark — _2026-11-13 Codex_

- [x] **Xác định cổng 8000 chạy GraphRAG riêng và mở For Your Future trên 8001**, kiểm tra HTML/CSS/health — _2026-11-13 Codex_

- [x] **Cải thiện độ tương phản dark/light**, CTA, badge, nền trong suốt, form và chữ phụ; kiểm tra Chrome — _2026-11-13 Codex_

- [x] **Nối JWT, hồ sơ đã lưu và kết quả trắc nghiệm vào tư vấn**, không dùng dữ liệu mẫu khi thiếu hồ sơ/Neo4j lỗi — _2026-11-13 Codex_

- [x] **Luồng sau đăng nhập: cá nhân/quê quán → học bạ/điểm thi → tài chính/thể lực (bỏ qua được) → trắc nghiệm**, lưu theo tài khoản — _2026-11-13 Codex_

- [x] **Thiết kế lại header responsive, không dồn chữ và không tràn ngang**, kiểm thử Chrome 320–1920px — _2026-11-13 Codex_

- [x] **Yêu cầu đăng nhập trước khi làm trắc nghiệm**, quay lại bài sau đăng nhập/đăng ký — _2026-11-13 Codex_
- [x] **Thêm tài khoản admin riêng và giao diện chỉ nhập mật khẩu**, bỏ khoảng trắng trong mật khẩu — _2026-11-13 Codex_

- [x] **Logo chính thức** vào header/footer/favicon — _2026-11-12 Antigravity_
- [x] **Seed 126 trường lên PostgreSQL Aiven** (126 unis, 3482 programs, 14547 criteria) — _2026-11-12 Antigravity_
- [x] **Trang chi tiết trường** `#truong-dai-hoc/uni-XXX` với API-first + fallback — _2026-11-12 Antigravity_
- [x] **Animated SVG cho 16 MBTI types** — _2026-11-12 Antigravity_
- [x] **RIASEC 3-avatar triplet renderer** (chữ đứng đầu to nhất) — _2026-11-12 Antigravity_
- [x] **Live badge** 🟢 trên trang danh sách 126 trường — _2026-11-13 Antigravity_
- [x] **Grouped program rows** (mỗi ngành 1 hàng, 8 cột) — _2026-11-13 Antigravity_
- [x] **Cột Học bạ + Học phí** trong bảng ngành — _2026-11-13 Antigravity_
- [x] **Hệ thống tài liệu chia sẻ AI** (AGENTS.md, PROJECT_CONTEXT, WORK_HISTORY, TODO) — _2026-11-13 Antigravity_

---

## 📌 KNOWN ISSUES

| Issue | Mức độ | Ghi chú |
|-------|--------|---------|
| Server cần bypass sandbox để khởi động | Medium | Uvicorn port binding cần quyền network |
| Một số trường thiếu điểm ĐGTD/Kết hợp | Low | Do dữ liệu Excel không có, không phải lỗi code |
| Neo4j container chưa được seed đầy đủ | Medium | Knowledge graph chưa sync với PostgreSQL data mới |
| Excel formula cells không resolve được | Info | Đã xử lý bằng `data_only=True` trong openpyxl |
| 46/126 trường không có học phí | Info | Excel nguồn không có thông tin |

