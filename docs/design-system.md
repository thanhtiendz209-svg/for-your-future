# HỆ THỐNG THIẾT KẾ GIAO DIỆN "FOR YOUR FUTURE"
**Bản chuẩn hóa kế thừa phong cách Trắc nghiệm tính cách (Trachngiemtinhcach)**

---

## 1. TỔNG QUAN & NGUYÊN TẮC THIẾT KẾ

Nền tảng **For Your Future** hướng đến đối tượng học sinh THPT, phụ huynh và sinh viên Việt Nam trong giai đoạn định hướng nghề nghiệp và chọn trường đại học. 

### Ba nguyên tắc cốt lõi:
1. **Luminous & Friendly (Nhẹ nhàng & Thân thiện):** Sử dụng nền sáng trắng ánh xanh (`#F6FAFD` Paper, `#F3F8FC` Mist, `#E8F3FB` Ice) kết hợp màu nhấn Navy đại dương (`#0B3A62`), Azure (`#1A6DB5`) và Cyan rực rỡ (`#2AB8C9`). Không tạo cảm giác nặng nề, áp lực thi cử hay khô khan dữ liệu.
2. **Clear & Structured (Rõ ràng & Có thứ bậc):** Thẻ thông tin bo góc lớn (24px), viền mảnh sắc nét (`#D5E4F0`), bóng đa tầng siêu nhẹ (`--shadow-border`). Điểm số, mức lương và chỉ tiêu tuyển sinh dùng phông số dạng bảng (`tabular-nums`) để đối chiếu nhanh.
3. **Empowering & Transparent (Đồng hành & Khách quan):** Ngôn từ tự nhiên, không phán xét. Kết quả trắc nghiệm và gợi ý chọn trường luôn minh bạch nguồn gốc (Đề án tuyển sinh 2026 chính thức của 126 trường Đại học, kiểm định ABET/AUN-QA), khích lệ người học trao đổi thêm cùng gia đình và thầy cô.

---

## 2. BẢNG MÀU THAM CHIẾU & SEMANTIC TOKENS

Toàn bộ biến CSS được khai báo tại `apps/web/public/styles.css` và cấu hình mở rộng trong Tailwind CDN:

| Tên Token | Mã Hex | Vai trò & Ứng dụng |
| :--- | :--- | :--- |
| **`--color-navy`** | `#0B3A62` | **Màu thương hiệu chính**: Nút bấm chính (CTA), tiêu đề cấp cao, icon box, thanh điều hướng. |
| **`--color-navy-deep`**| `#082A48` | **Trạng thái Hover/Active** của nút chính, viền nhấn đậm, văn bản bôi đen (`::selection`). |
| **`--color-azure`** | `#1A6DB5` | **Màu nhấn thứ nhất**: Eyebrow tags, links, chỉ số nổi bật, viền trạng thái được chọn (`.is-on`). |
| **`--color-cyan`** | `#2AB8C9` | **Màu nhấn thứ hai**: Điểm nhấn công nghệ, vòng tròn la bàn, glow hiệu ứng, nhãn bước (01, 02...). |
| **`--color-cyan-soft`**| `#7EDCE6` | **Màu phát sáng phụ**: Vòng ngoài logo la bàn, viền phụ trên nền tối. |
| **`--color-ice`** | `#E8F3FB` | **Nền nhấn nhạt**: Nền hộp icon, nền lựa chọn đã chọn (`.is-on`), pill tag, nền logo trường. |
| **`--color-mist`** | `#F3F8FC` | **Nền phân khu nhẹ**: Nền dải RIASEC, nền bảng dữ liệu so sánh, nền input field. |
| **`--color-paper`** | `#F6FAFD` | **Nền canvas chính**: Nền toàn trang, header frosted glass, footer. |
| **`--color-card`** | `#FFFFFF` | **Nền thẻ nội dung**: Bề mặt các card trắc nghiệm, trường ĐH, biểu mẫu hồ sơ. |
| **`--color-ink`** | `#12304A` | **Văn bản chính**: Tiêu đề bài viết, nội dung đọc chính, độ tương phản chuẩn WCAG AA. |
| **`--color-muted`** | `#5B7590` | **Văn bản phụ**: Mô tả chi tiết, hướng dẫn, nhãn phụ, ngày tháng, thông số kỹ thuật. |
| **`--color-line`** | `#D5E4F0` | **Đường viền chuẩn**: Viền card 24px, viền input, đường phân cách accordion. |
| **`--color-danger`** | `#9A3B3B` | **Trạng thái cảnh báo/lỗi**: Điểm chuẩn chênh lệch âm (Vươn tới), thông báo lỗi đăng nhập. |
| **`--color-success`**| `#15803D` | **Trạng thái an toàn/thành công**: Phân nhóm Safe, huy hiệu Zero-Hallucination. |
| **`--color-warning`**| `#B45309` | **Trạng thái mục tiêu**: Phân nhóm Target, lưu ý điều kiện sơ tuyển. |

---

## 3. TYPOGRAPHY (HỆ THỐNG KIỂU CHỮ)

* **Font Tiêu đề (Display / Headings):** `Plus Jakarta Sans` (weights: 600, 700, 800) với tính chất hình học hiện đại, kerning chặt chẽ (`letter-spacing: -0.025em`) mang lại nét trẻ trung, quyết đoán.
* **Font Nội dung (Body Text):** `Be Vietnam Pro` (weights: 400, 500, 600, 700), được thiết kế tối ưu riêng cho hệ thống ký tự và dấu tiếng Việt, mang lại trải nghiệm đọc mượt mà, không bị lỗi hiển thị dấu ở các ký tự phức tạp (như ệ, ỗ, ứ, ở).
* **Font Số liệu bảng biểu (Tabular Numerals):** `tabular-nums` đảm bảo các cột điểm chuẩn (25.50, 28.20), học phí (33,000,000 VND) và tỷ lệ tăng trưởng (+18%) luôn thẳng hàng tuyệt đối.

### Thang đo tỷ lệ (Type Scale):
* **H1 Hero:** `36px – 48px` / Line-height `1.15` / Weight `800`
* **H2 Section Title:** `24px – 32px` / Line-height `1.2` / Weight `700`
* **H3 Card Title:** `18px – 20px` / Line-height `1.3` / Weight `700`
* **Body Main:** `15px – 16px` / Line-height `1.6` / Weight `400`
* **Body Small / Captions:** `12px – 13px` / Line-height `1.5` / Weight `500`
* **Eyebrow / Category Tag:** `11px – 12px` / Uppercase / `letter-spacing: 0.16em` / Weight `700`

---

## 4. RADIUS, SHADOWS & MOTION (BO GÓC, ĐỔ BÓNG & CHUYỂN ĐỘNG)

### Bo góc (Border Radii):
* **Card lớn (Thẻ nội dung, Banner, Form):** `24px – 28px` (`rounded-[24px]` hoặc `rounded-[28px]`).
* **Nút bấm & Ô nhập liệu (Buttons & Inputs):** `12px – 14px` (`rounded-[12px]` hoặc `rounded-[14px]`).
* **Badge / Tag nhãn / Bộ lọc Chip:** `9999px` (`rounded-full`).
* **Hộp Icon / Logo trường:** `14px` (`rounded-[14px]`).

### Đổ bóng (Layered Soft Shadows):
* **`--shadow-border`:** Đổ bóng viền tinh tế kết hợp viền 1px mờ nhẹ:
  `0px 0px 0px 1px rgba(18, 48, 74, 0.06), 0px 1px 2px -1px rgba(18, 48, 74, 0.06), 0px 2px 4px 0px rgba(18, 48, 74, 0.04)`
* **`--shadow-border-hover`:** Đổ bóng nâng cao khi hover vào thẻ:
  `0px 0px 0px 1px rgba(18, 48, 74, 0.1), 0px 10px 28px -12px rgba(11, 58, 98, 0.22)`
* **`--shadow-cta` (CTA Glow):** Hiệu ứng phát sáng màu Azure cho nút hành động chính:
  `0 10px 24px -10px rgba(26, 109, 181, 0.55)`

### Hiệu ứng chuyển động (Micro-interactions):
* **`float-slow` & `float-slower`:** Chuyển động bồng bềnh nhẹ nhàng 5.5s – 7.5s cho ảnh minh họa hero nhân vật và thẻ hồ sơ mẫu.
* **`.option-card`:** Thao tác chọn câu trả lời mượt mà: `translateY(-2px)` khi rê chuột, co nhẹ `scale(0.985)` khi bấm, chuyển viền sang Azure và nền sang Ice khi kích hoạt (`.is-on`).
* **`.bar-fill`:** Hiệu ứng thanh năng lực RIASEC nở ra từ trái sang phải (`scaleX(0)` → `scaleX(1)`) trong 650ms.
* **Hỗ trợ `prefers-reduced-motion`:** Tự động tắt toàn bộ animation và transition khi người dùng bật chế độ giảm chuyển động trên thiết bị.

---

## 5. THƯ VIỆN COMPONENTS CHUẨN

1. **Header Frosted Glass:**
   - Nền `bg-paper/85` với `backdrop-blur-xl`, viền mảnh `border-line`.
   - Logo la bàn tọa độ kép SVG trong khối bo 12px navy.
   - Menu điều hướng dạng viên thuốc (pills) với trạng thái active là `bg-ice text-navy font-semibold`.
2. **Hero Hai Cột (Two-column Hero):**
   - Nền loang đa bán kính `.hero-wash` (cyan/azure).
   - Khối thông điệp truyền cảm hứng bên trái, minh họa nhân vật học sinh bên phải với thẻ mẫu INFP lơ lửng.
3. **Thẻ Trắc Nghiệm Option Card:**
   - Thang đo Likert 5 mức độ từ "Rất không thích" đến "Rất yêu thích".
   - Kích thước lớn, thân thiện với cảm ứng màn hình điện thoại.
4. **Bộ Lọc Cắt Tỉa Tuyển Sinh (Recommendation Filter):**
   - Ô nhập điểm, chọn tổ hợp môn, trần ngân sách, chiều cao, thị lực.
   - Nút "⚡ Nạp nhanh từ Hồ sơ học tập" tự động đồng bộ dữ liệu PostgreSQL vào form chỉ với 1 click.
5. **Thẻ Kết Quả Nguyện Vọng (Recommendation Card):**
   - Phân loại rõ 3 nhóm: 🟢 **An toàn (Safe)**, 🟡 **Mục tiêu (Target)**, 🔴 **Vươn tới (Reach)**.
   - Thể hiện: Tên trường, Mã ngành, Điểm chuẩn, Điểm sàn, Tiêu chí phụ (tie-breaker), Học phí/năm, Link Đề án gốc và nút "Hỏi Cố vấn AI".
6. **Cố Vấn Tuyển Sinh AI Drawer:**
   - Cửa sổ kéo từ mép phải với nền Paper/Card sang trọng.
   - Khối tin nhắn AI có huy hiệu "Zero-Hallucination GraphRAG", tự động trích dẫn bằng chứng đề án.

---

## 6. BẢNG ĐỐI CHIẾU PHONG CÁCH CŨ VÀ MỚI

| Tiêu chí | Bản Giao Diện Cũ (Prototype) | Bản Giao Diện Mới (For Your Future Chuẩn Hóa) |
| :--- | :--- | :--- |
| **Màu sắc chủ đạo** | Màu xám xỉn Slate (`#f8fafc`, `#334155`), màu xanh Tailwind mặc định (`#0284c7`). | Bảng màu Luminous đại dương: Navy (`#0B3A62`), Azure (`#1A6DB5`), Cyan (`#2AB8C9`), Ice (`#E8F3FB`), Paper (`#F6FAFD`). |
| **Typography** | Font hệ thống mặc định (`font-sans`), không tối ưu hiển thị tiếng Việt. | Tiêu đề **`Plus Jakarta Sans`**, Nội dung **`Be Vietnam Pro`** chuẩn tiếng Việt 100%, số liệu **`tabular-nums`**. |
| **Bo góc thẻ** | Bo góc nhỏ `rounded-lg` hoặc `rounded-xl` (12px), viền thô. | Bo góc lớn hiện đại **`24px – 28px`**, viền sắc mảnh siêu tinh tế (`#D5E4F0`). |
| **Nút bấm & Tương tác**| Nút bấm màu xanh phẳng, không có hiệu ứng cọ xát thị giác. | Nút Navy sâu với hiệu ứng **`cta-glow`**, **`option-card`** phản hồi mượt mà qua hover/active/selected. |
| **Bố cục Hero** | 1 cột căn giữa đơn điệu, toàn chữ. | **Hero 2 cột** sống động: Thông điệp bên trái, tác phẩm minh họa nhân vật học sinh bên phải với badge nổi. |
| **Quy trình trải nghiệm**| Rời rạc, chưa tạo sự liên kết giữa trắc nghiệm và chọn trường. | **Hành trình 4 bước** khép kín: Hiểu bản thân → Khám phá nghề → Chọn ngành/trường → Cố vấn AI có nguồn. |
| **Thẻ kết quả tuyển sinh**| Khối danh sách đơn giản, thiếu thông số tiêu chí phụ. | Thẻ chuẩn hóa đầy đủ: Điểm sàn, điểm chuẩn, môn tiêu chí phụ, học phí niêm yết, link đề án gốc, nút hỏi AI. |

---

## 7. HƯỚNG DẪN KIỂM TRA ĐA KÍCH THƯỚC MÀN HÌNH

Hệ thống đã được thiết kế đáp ứng hoàn toàn (Fully Responsive) không gây hiện tượng thanh cuộn ngang (horizontal scrollbar):

1. **Mobile (375px – 430px) - iPhone SE, iPhone 14/15 Pro, Pixel 7:**
   - Header tự động thu gọn menu thành nút mở Drawer trượt mượt mà.
   - Thang đo 5 mức Likert trắc nghiệm tự động chuyển thành danh sách dọc dễ chạm ngón tay cái.
   - Thẻ trường học hiển thị 1 cột, đầy đủ thông số điểm chuẩn và học phí.
2. **Tablet (768px – 834px) - iPad Air, iPad Mini:**
   - Lưới trường học và ngành nghề hiển thị 2 cột cân đối.
   - Form trắc nghiệm và hồ sơ học sinh hiển thị 2 cột input khoa học.
3. **Desktop (1024px – 1440px+) - MacBook, Laptop Full HD, Màn hình 2K/4K:**
   - Hero 2 cột tỷ lệ vàng `1.1fr : 0.9fr`.
   - Lưới trường học 3 cột mượt mà, cố định chiều rộng nội dung tối đa `max-w-6xl` (1152px) giúp mắt người đọc không bị mỏi khi quét ngang.

