# Mục “dữ liệu người dùng” trên Aiven

Vị trí: cơ sở dữ liệu `defaultdb` → schema `public` → **Views** → **dữ liệu người dùng**. Làm mới danh sách đối tượng nếu chưa thấy mục này.

```sql
SELECT * FROM public."dữ liệu người dùng"
ORDER BY "Ngày đăng ký" DESC, "Mã người dùng";
```

Mỗi tài khoản có đúng một dòng, kể cả tài khoản chưa có hồ sơ. Các cột gồm email đăng nhập, họ tên, ngày sinh, giới tính, số điện thoại, trường đang học, lớp, năm xét tuyển, tỉnh/thành, vai trò, trạng thái và ngày đăng ký. Học bạ/điểm thi, tài chính/khu vực ưu tiên, thể lực và kết quả bốn bài test nằm trong các cột JSON có thể mở xem hoặc xuất bằng công cụ cơ sở dữ liệu.

Các bảng nguồn vẫn lưu dữ liệu như trước. View chỉ tổng hợp khi truy vấn, luôn đọc dữ liệu đã được lưu thành công trên Aiven tại thời điểm đó. Không có tác vụ đồng bộ, trigger, API, trang web mới hay thay đổi AI. Không chứa mật khẩu hoặc mã băm mật khẩu; không cấp quyền cho PUBLIC.

Kết quả RIASEC, MBTI, Big Five lấy lần hoàn thành mới nhất theo từng loại; năng lực nhận thức lấy loại `INTERNAL`. Bài chưa làm/chưa đồng bộ và hồ sơ thiếu sẽ là `NULL`. Nhiều bản ghi cùng thời gian được chọn ổn định theo ID. Điểm được giữ nguyên, không tính lại hay quy đổi. Không đưa trường `percentile` vào báo cáo vì giá trị hiện tại không phải thứ hạng phần trăm chuẩn hóa.

View không thu thập thêm thông tin từ trình duyệt và không giữ bản sao lịch sử khi nguồn bị sửa/xóa. Dữ liệu chỉ lưu cục bộ trên trình duyệt, chưa gửi API, sẽ chưa xuất hiện. Các mốc thời gian giữ nguyên giá trị UTC của ứng dụng.

Nguồn SQL: `scripts/sql/user_data_report.sql`. Dùng `CREATE VIEW`, không thay thế đối tượng đã có. Chỉ chạy trong một giao dịch với timeout ngắn sau khi đã xác nhận đúng Aiven. Không sửa schema/bảng nguồn. Truy vấn báo cáo vẫn dùng chung tài nguyên cơ sở dữ liệu.
