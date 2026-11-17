# Tối ưu giao diện — 2026-11-16

App 3.11.0 / styles 2.11.0 / utilities 1.0.0. Giữ SPA thuần JavaScript, các tuyến, dữ liệu/chấm điểm, phong cách và backend/AI.

- Dữ liệu JSON bắt buộc lúc vào trang chủ: **901.524 byte**, trước đó **4.498.574 byte** (giảm 80% riêng phần dữ liệu JSON ban đầu, chưa tính cache/nén). Chi tiết trường được tải khi vào Bộ lọc/tra cứu/trường/so sánh; tổ hợp RIASEC khi mở nhóm tính cách, kết quả RIASEC hoặc chọn tab RIASEC trên trang chủ.
- Mỗi file chỉ tải một lần trong một lần mở website, gộp yêu cầu đồng thời. Nếu lỗi, có thể thử lại. Khi chuyển trang trong lúc đang tải, trang cũ không ghi đè trang mới. Mọi bản ghi nguồn giữ nguyên.
- Tailwind được tạo sẵn thành `utilities.css` khoảng 50 KB. Không tải/chạy trình biên dịch CSS khoảng 407 KB và bộ theo dõi thay đổi DOM của Tailwind trong trình duyệt nữa. Lucide 1.73.0 và marked 15.0.12 được phục vụ cục bộ từ `vendor/`, giữ phiên bản đang dùng và kèm giấy phép.
- Lucide chỉ chuyển icon mới, không thay lại các SVG đã hiển thị. Danh sách tỉnh/phương thức/ngành được dùng lại đến khi bộ dữ liệu trường đổi.
- Ảnh quiz dùng bản tĩnh khi ở ngoài màn hình, tab bị ẩn hoặc người dùng chọn giảm chuyển động; tiếp tục ảnh động gốc khi thấy lại. Ảnh đồng sáng lập tạm dừng animation khi không thấy. Thu hồi đối tượng theo dõi khi rời trang. Không thêm thư viện theo dõi hay thay ảnh gốc.

## Khi sửa giao diện về sau

Chạy từ thư mục gốc sau khi đổi class trong HTML/JS/JSON:

```bash
node --check apps/web/public/app.js
node scripts/build_web_styles.cjs
node --test tests/*.test.cjs
```

Lệnh build dùng các phụ thuộc web đã có, đọc `apps/web/tailwind.static.cjs`, quét HTML/JS/JSON trong public và tạo utilities.css cho cả public/dist. Vẫn đồng bộ các file nguồn đã đổi và tăng phiên bản cache tương ứng trong index.html. Không thêm lại Tailwind CDN.

## Phạm vi kiểm tra

19 kiểm thử Node đạt: đăng nhập/làm bài, đồng bộ kết quả, chat 5 phút, bộ lọc, dữ liệu tải theo trang/gộp request/thử lại và tránh ghi đè trang mới. Chrome mô phỏng 320/390/768/1440px sáng/tối với dữ liệu JSON thật và API giả lập: 9 trang không tràn ngang, tab RIASEC có đủ 120 tổ hợp, bốn bài chọn đáp án/chuyển câu, chat SSE/Markdown và lịch sử đóng mặc định. Xác minh icon cũ giữ nguyên DOM, trạng thái ảnh đổi theo viewport/ẩn tab/reduced-motion, bộ theo dõi được giải phóng.

Kiểm tra trình duyệt dùng document được nạp trực tiếp vì công cụ Chrome ở môi trường này gặp lỗi điều hướng; ảnh gốc được nhúng để kiểm tra screenshot. Xác minh riêng các tài sản thật trên HTTP cổng 8000 khớp source/dist. Chưa đo FPS hoặc thời gian tải trên thiết bị iOS/Android thật; số giảm 80% là dung lượng dữ liệu JSON ban đầu, không phải cam kết tốc độ toàn trang tăng 80%.
