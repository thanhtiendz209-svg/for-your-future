# docs/WORK_HISTORY.md — Lịch sử Công việc

> **Quy tắc**: Luôn thêm entry mới vào **ĐẦU** file (prepend). Không xóa entry cũ.  
> **Format**: `## [YYYY-MM-DD] [AI] — [Mô tả ngắn]`

---


## [2026-11-18] Antigravity — Khắc phục GitHub Push Protection (loại bỏ thông tin bí mật khỏi Git)

**Agent**: Antigravity  
**Thời gian**: 2026-11-18 00:26 (GMT+7)  
**Files đã thay đổi**:
- `.env.example` — Thay mật khẩu thật Aiven/Neo4j bằng giá trị mẫu an toàn; bổ sung template biến GEMINI_API_KEY.
- `.gitignore` — Bổ sung mẫu loại trừ chuẩn `.env`, `.env.*`, `*.env`, lock files, pycache; bảo toàn `!.env.example`.
- `apps/api/app/core/config.py` — Thay mật khẩu Aiven thật trong chuỗi fallback mặc định bằng giá trị mẫu; giữ nguyên cơ chế đọc biến môi trường từ apps/api/.env.
- `docs/CODEX_PROMPT.md` — Che chuỗi mật khẩu Aiven bằng `***` theo quy tắc bảo mật.
- `infrastructure/docker-compose.yml` — Chuyển các giá trị nhạy cảm (DATABASE_URL, ASYNC_DATABASE_URL, NEO4J_PASSWORD, GEMINI_API_KEY) sang biến môi trường (`${VAR}`).

**Kết quả**:
- ✅ Toàn bộ mật khẩu Aiven thật đã được loại bỏ 100% khỏi các file theo dõi trong Git.
- ✅ Cấu hình backend FastAPI và Docker Compose tiếp tục nạp biến môi trường chuẩn xác từ local `.env`.
- ✅ Quét kiểm tra toàn bộ workspace xác nhận chỉ còn duy nhất file cục bộ `apps/api/.env` (được gitignore hoàn toàn) lưu thông tin kết nối thực tế.
- ✅ Commit ban đầu được amend an toàn, sẵn sàng đẩy lên GitHub.

**Lưu ý cho AI tiếp theo**:
- Thông tin nhạy cảm của Aiven và Neo4j chỉ nằm tại `apps/api/.env` (untracked, quyền cục bộ). Tuyệt đối không commit file này lên git.

---


## [2026-11-17] Codex — Cập nhật khóa Gemini và kết nối Neo4j theo yêu cầu

**Ủy quyền**: người dùng cung cấp khóa Gemini mới cùng URI/user/password/database Neo4j Aura và yêu cầu thay cấu hình; yêu cầu đưa lên GitHub đã được người dùng hủy. Không tạo repository, commit, push hoặc tải mã lên GitHub. Chỉ đã đọc hồ sơ/danh sách repository qua connector trước khi hủy.

**Files**: apps/api/.env (chỉ lưu cục bộ, quyền 0600), apps/api/app/core/config.py, apps/api/app/modules/graphrag/llm_service.py.

- Thay đúng năm giá trị GEMINI_API_KEY và NEO4J_URI/USER/PASSWORD/DATABASE trong .env; chuẩn hóa URI bỏ dấu escape từ tin nhắn. Không ghi giá trị bí mật vào tài liệu.
- Config đọc apps/api/.env bằng đường dẫn tuyệt đối để chạy từ thư mục gốc hay apps/api đều thống nhất. Bỏ khóa Gemini mặc định cứng; LLM dùng settings.GEMINI_API_KEY, settings.GEMINI_MODEL và base URL hiện có thay vì đọc os.getenv riêng nên nhận đúng khóa mới.
- Các giá trị môi trường khác, đặc biệt DATABASE_URL/ASYNC_DATABASE_URL của Aiven, được đối chiếu giữ nguyên. Không sửa thuật toán AI, truy vấn graph, chấm điểm hoặc frontend. Hash các file Python còn lại giữ nguyên.

**Kiểm tra**: compileall đạt; import từ cwd gốc xác nhận cả settings/LLM đọc khóa mới và đúng bốn thông số Neo4j; yêu cầu Gemini ngắn trả HTTP 200/có nội dung; Neo4j xác thực và truy vấn chỉ đọc database người dùng cung cấp thành công, 18376 node. Không chuyển/seed/xóa dữ liệu graph.

**Chạy web**: trước thay đổi không có tiến trình cổng 8000 và không có dịch vụ systemd for-your-future đang chạy; đã khởi động uvicorn app.main:app tại apps/api, host 0.0.0.0:8000. /health và /api/v1/admin/health HTTP 200, trạng thái healthy. Không cài hoặc bật systemd/tunnel công khai.

---


## [2026-11-16] Codex — Giảm tải và công việc dựng giao diện trên điện thoại/máy tính

**Files**: public/app.js, styles.css, index.html, utilities.css, vendor/* và dist; apps/web/tailwind.static.cjs; scripts/build_web_styles.cjs; tests/performance.test.cjs; AGENTS.md; docs/WEB_PERFORMANCE.md. App 3.11.0 / CSS 2.11.0 / utilities 1.0.0.

- JSON đầu trang chủ giảm từ 4498574 xuống 901524 byte (80% riêng JSON). Tải school_details theo các trang trường/Bộ lọc/tra cứu/so sánh, riasec_combinations theo trang nhóm/kết quả hoặc tab RIASEC ở home. Gộp yêu cầu, cache trong phiên, lỗi cho phép thử lại; kiểm tra phiên render để trang tải chậm không đè trang vừa mở. Core JSON độc lập, một file lỗi không làm mất mọi bộ dữ liệu đã tải thành công.
- Thay Tailwind CDN/runtime compiler bằng utilities.css tạo sẵn từ cùng design config. Self-host đúng Lucide 1.73.0/marked 15.0.12 đã dùng, giữ giấy phép; không đổi provider AI hoặc framework. Thêm lệnh build trong AGENTS/docs để các lần đổi class tiếp theo không mất CSS.
- Refresh icon chỉ xử lý placeholder mới qua nameAttr riêng, giữ các SVG cũ. Cache danh sách lựa chọn Bộ lọc theo nguồn universities.
- Một IntersectionObserver dùng chung cho hero/ảnh quiz: tạm dừng hero hoặc dùng SVG tĩnh khi ngoài màn hình/ẩn tab/reduced-motion, tiếp tục khi xuất hiện; bỏ theo dõi DOM cũ khi đổi route. Ảnh gốc không chỉnh sửa, nội dung/style/tuyến/chấm điểm giữ nguyên.

**Kiểm tra**: Node syntax và 19 test đạt. Chrome document fixture với CSS/thư viện nguồn, JSON thật/API giả: 9 trang × 4 viewport × sáng/tối không tràn; home RIASEC đủ 120 tổ hợp; bốn quiz chọn đáp án tự chuyển câu; chat SSE ra đủ Markdown, lịch sử mặc định đóng; ảnh đổi nguồn theo viewport/ẩn tab/reduced-motion và theo dõi được thu hồi; refreshIcons lặp giữ nguyên node icon. Đã xem ảnh home mobile sáng/desktop tối nhúng ảnh gốc. Giới hạn: Chrome điều hướng môi trường lỗi, fixture nạp document trực tiếp; chưa đo FPS/thiết bị thật. Số liệu 80% không phải tăng tốc toàn website 80%.

**Triển khai**: tài sản public/dist/HTTP cổng 8000 đối chiếu byte, health 200. Không restart backend, không đổi cấu hình/schema/dữ liệu Aiven. SHA256 các file API/AI và ảnh Drive gốc giữ nguyên. Chi tiết tại docs/WEB_PERFORMANCE.md.

---


## [2026-11-16] Codex — Thay minh họa bốn bài test bằng SVG động từ Drive

**Files**: public/app.js, index.html, data/quizzes.json, illustrations/quiz-{riasec,cognitive,bigfive,mbti}-{animated,still}.svg và dist tương ứng. App 3.10.4; CSS giữ 2.10.3.

Tải `anh-dong.zip` từ thư mục Drive người dùng chỉ định bằng file_uri chuẩn. Chỉ lấy bốn SVG: riasec-dong → RIASEC, nhan-thuc-dong → Năng lực nhận thức, big-five-dong → Big Five, mbti-dong → MBTI. SVG động nguyên bản giữ nguyên byte (tổng khoảng 64KB); xác nhận không có script/foreignObject/event handler/tham chiếu tài nguyên ngoài. Không chạy file demo HTML trong ZIP.

Cập nhật cả quizzes.json và dữ liệu fallback, dùng cùng renderer ở trang chủ và trang danh sách bài test. Khung 4:3/object-contain cho đúng viewBox 800×600, bỏ badge icon nhỏ chồng lên ảnh và zoom crop; giữ nội dung, thứ tự ưu tiên và nút/link làm bài/kết quả. Ảnh lazy/async có kích thước khai báo. Picture chọn bản SVG đứng yên khi prefers-reduced-motion; bản đứng yên chỉ thêm CSS animation:none/transition:none, không thay đổi bản động gốc. Không thêm thư viện, không chỉnh chấm điểm/AI.

**Kiểm tra**:
- Node syntax và quiz-auth regression đạt; renderer chọn đúng bốn đường dẫn và liên kết test ở data/fallback.
- Chrome kiểm tra thành phần dựng bằng renderer/CSS/font/ảnh nguồn: 320/390/768/1440px sáng/tối, đủ bốn ảnh, không tràn, tỷ lệ 4:3/object-contain. Đối chiếu screenshot từng ảnh cách nhau một giây: cả bốn thay đổi; giảm chuyển động: cả bốn ảnh đứng yên. Đã xem desktop sáng. Đây là kiểm tra renderer thành phần, không phải toàn bộ luồng làm bài.
- 11 tài sản public/dist/HTTP cổng 8000 khớp từng byte, MIME image/svg+xml đúng; bốn animation khớp ZIP. SHA256 toàn bộ API/AI giữ nguyên.

---


## [2026-11-16] Codex — Hai khung tên trong ảnh và ảnh tự chuyển động nhẹ

**Files**: public/app.js, styles.css, index.html và dist. App 3.10.3 / CSS 2.10.3.

Bỏ avatar chữ NQ/TT và khung chung dưới ảnh. Hai khung độc lập, mỗi khung ghi Đồng sáng lập và đầy đủ tên: Quỳnh ở vùng trống trên trái, Tiến ở vùng trống dưới phải. Dùng vị trí theo phần trăm và cỡ chữ theo container để giữ khung trong ảnh ở điện thoại/desktop; nền theo theme, viền xanh, không che mặt/logo. Ảnh và hai khung cùng nổi lên/xuống 6px theo chu kỳ 7 giây, không cần di chuột; giữ glow nhẹ. Reduced-motion tắt chuyển động. PNG và CSS xoay ảnh gốc giữ nguyên.

**Kiểm tra**: Node syntax/PostCSS parse; component Chrome 320/390/768/1440px, sáng/tối: hai khung nằm trong ảnh/vùng trống, tên không tràn, không còn chữ viết tắt, animation ảnh có hiệu lực và reduced-motion tắt. Đã xem screenshot mobile sáng và desktop tối. Kiểm tra riêng component bằng markup/CSS/fonts/ảnh nguồn như đợt trước, không khẳng định kiểm thử toàn trang. Source/dist khớp; HTTP cổng 8000 phục vụ đúng các tài sản mới. Ảnh gốc và SHA256 toàn bộ API/AI không đổi.

---


## [2026-11-16] Codex — Làm nổi bật ô đồng sáng lập và thêm chuyển động

**Files**: public/app.js, styles.css, index.html và ba file dist tương ứng. App 3.10.2 / CSS 2.10.2.

Thiết kế caption thành thẻ viền gradient xanh, nền có điểm sáng dịu và bóng rõ hơn, nhãn Đồng sáng lập dạng pill với icon nét users-round. Hai tên giữ nguyên, mỗi người một hàng với avatar chữ NQ/TT để phân biệt trực quan. Thẻ nổi nhẹ theo chu kỳ 7 giây, ánh sáng lướt chu kỳ 9 giây; hover hàng tên dịch nhẹ, avatar xoay/nhích. Chỉ animation transform/opacity của lớp trang trí; không thêm thư viện hoặc listener JS. Reduced-motion tắt float/shine/hover motion; điện thoại giảm đệm/avatar và giữ chữ dễ đọc. Ảnh gốc và chiều xoay giữ nguyên.

**Kiểm tra**:
- Node syntax và PostCSS parse đạt, public/dist khớp. PNG gốc không đổi, SHA256 toàn bộ API/AI vẫn khớp.
- Chrome gặp lỗi điều hướng (tab vẫn about:blank), nên kiểm tra riêng component bằng chính markup/CSS/fonts/ảnh nguồn nhúng vào document, không sửa code website để phục vụ test. Viewport đúng meta mobile: 320/390/768/1440px sáng/tối đều không tràn, hai tên nằm trong thẻ, float/shine CSS có hiệu lực; reduced-motion tắt cả hai. Đã xem screenshot mobile sáng và desktop tối sau khi transition theme kết thúc. Đây là kiểm tra thành phần, chưa phải kiểm tra toàn trang trong đợt này.
- HTTP cổng 8000 phục vụ đúng từng byte ba file cập nhật. Không đổi backend, AI, dữ liệu hoặc cấu trúc điều hướng.

---


## [2026-11-16] Codex — Thay ảnh trang chủ và giới thiệu hai đồng sáng lập

**Files**: public/app.js, styles.css, index.html, illustrations/co-founders.png và bốn file tương ứng trong dist. App 3.10.1 / CSS 2.10.1.

Theo ảnh Drive người dùng chỉ định, thay riêng ảnh hero và nhãn “Hồ sơ mẫu / INFP · Người lý tưởng” bằng “Đồng sáng lập”, “TRỊNH THỊ NHƯ QUỲNH”, “NGUYỄN THÀNH TIẾN”. Tách hai tên thành hai dòng, đặt caption dưới ảnh, bo góc và nền theo theme. PNG gốc 479×640, 205105 bytes được giữ nguyên; ảnh gốc nằm ngang theo chiều xoay nên dùng CSS rotate(-90deg), khung 640/479 hiển thị toàn ảnh, không cắt nội dung. Chỉ trang trí vùng hero bằng quầng sáng xanh thay đổi opacity chậm, nâng nhẹ khi hover chuột; reduced-motion tắt hiệu ứng. Không thêm thư viện hoặc JS chạy theo chuột.

**Kiểm tra**:
- Node syntax đạt; bốn tài sản public/dist giống từng byte. PNG khớp bản tải từ file_uri chuẩn của Google Drive; 78 file API/AI giữ nguyên SHA256.
- Chrome headless trên máy chủ tĩnh cùng source public, viewport 320/390/768/1440px sáng/tối: không tràn ngang, toàn ảnh đúng tỷ lệ, tên nằm trong caption, nhãn cũ đã bỏ, reduced-motion tắt glow. Đã xem screenshot desktop sáng và điện thoại tối.
- Xác nhận cổng 8000 phục vụ đúng bốn tài sản vừa kiểm tra (SHA256), không restart dịch vụ, không thay đổi dữ liệu hoặc AI.

**Lưu ý**: Lần điều hướng trực tiếp Chrome tới cổng 8000 bị timeout; kiểm tra bố cục dùng máy chủ tĩnh tạm, đã tắt sau kiểm tra. Tải ảnh ban đầu qua nhật ký bị auto-review từ chối; đã chuyển sang tải chuẩn trực tiếp từ kết quả công cụ Drive và thành công, không dùng nhật ký để lấy file. Không thay đổi quyền chia sẻ/file gốc trên Drive.

---


## [2026-11-16] Codex — Tạo mục “dữ liệu người dùng” trên Aiven

**Thời gian**: 2026-11-16 21:07 (GMT+7). **Ủy quyền**: người dùng yêu cầu tạo mục chỉ tổng hợp dữ liệu trên tài khoản Aiven hiện tại, giữ nguyên website/AI.

**Migration dự kiến (ghi trước khi thay đổi schema)**: thêm duy nhất view `public."dữ liệu người dùng"` vào `defaultdb`, theo `scripts/sql/user_data_report.sql`. Một dòng/tài khoản, tổng hợp hồ sơ/địa phương/trường, học bạ/điểm thi, tài chính/thể lực và kết quả mới nhất RIASEC/MBTI/Big Five/INTERNAL. LEFT JOIN LATERAL LIMIT 1 tránh nhân dòng. Không chứa password_hash; không đổi bảng nguồn, trigger, API, AI, cấu hình hay kết nối. REVOKE ALL FROM PUBLIC chỉ trên view mới. Không thay thế đối tượng đã có.

**Kết quả**: đã tạo và commit duy nhất view trên Aiven; xác nhận lại qua kết nối mới. Có 21 cột và 5 dòng cho 5 tài khoản, không nhân dòng; hiện 2 người có RIASEC, 1 người có INTERNAL, MBTI/Big Five chưa có bản ghi nên để NULL. Không tạo tài khoản DB mới hoặc cấp quyền thêm. Hướng dẫn xem tại `docs/USER_DATA_REPORT.md`.

**Kiểm tra**:
- SQL thật chạy trên các bảng/view tạm với dữ liệu giả rồi rollback: đúng chủ tài khoản, một dòng dù nhiều hồ sơ/kết quả, thiếu hồ sơ/bài test vẫn giữ dòng, lấy mới nhất/tie theo ID, giữ điểm 0, tách INTERNAL khỏi V-ACT, phản ánh cập nhật nguồn, không có password_hash, UPDATE bị PostgreSQL từ chối (55000).
- View thật được PostgreSQL xác nhận không cho UPDATE/INSERT, không có quyền PUBLIC; ID kết quả của bốn loại khớp truy vấn nguồn độc lập; fingerprint cả bảy bảng nguồn trước/sau giống nhau.
- SHA256 của 84 file mã API và frontend public/dist giữ nguyên; không sửa AI, không restart dịch vụ. Website health HTTP 200 trước và sau.

**Giới hạn**: view đọc dữ liệu đã lưu trên Aiven, không sao lưu lịch sử, không thu dữ liệu chỉ còn trên trình duyệt. Giữ timestamp UTC và điểm nguồn; bỏ percentile chưa chuẩn hóa. Không có job/trigger hay chức năng mới trên website.

---


## [2026-11-16] Codex — Hoàn tác phần nối kết quả bốn bài test vào AI

Theo xác nhận của người dùng, chỉ gỡ thay đổi backend vừa thực hiện để đọc MBTI, Big Five và năng lực nhận thức vào ngữ cảnh AI; giữ nguyên giao diện đã chốt. Xóa module assessment_context mới và các chỗ tích hợp trong router, intent_classifier, graph, service, llm_service. Khôi phục cách đọc RIASEC mới nhất và luồng tư vấn trước đợt này.

Kiểm tra: compileall các file Python liên quan đạt; không còn tham chiếu đến module/ngữ cảnh mới. Phần sửa vừa rồi chưa khởi động lại hay triển khai vào tiến trình server. Không sửa frontend, dữ liệu người dùng, schema hoặc cấu hình DB.

---



## [2026-11-15] Codex — Người dùng chốt bản tối ưu, bỏ bản sao lưu

Người dùng chấp nhận bản hiện tại App 3.10.0 / CSS 2.10.0 và không cần bản sao lưu nữa. Theo yêu cầu, đã xóa riêng backups/mobile-ux-20261115-baseline/ và scripts/restore_mobile_20261115.py của đợt này. Sáu file frontend public/dist được đối chiếu SHA256 trước/sau và giữ nguyên; không hoàn tác giao diện. Các ghi nhận backup ở entry lịch sử trước không còn áp dụng.

---

## [2026-11-15] Codex — Tối ưu điện thoại và render, có bản khôi phục đầy đủ

**Files**: public/app.js, styles.css, index.html và dist; scripts/restore_mobile_20261115.py; backups/mobile-ux-20261115-baseline/. App 3.10.0, CSS 2.10.0.

**Giới hạn**: giữ routes, thứ tự nội dung, màu sắc/fonts, ảnh minh họa, dữ liệu, chấm điểm, backend/AI và quy tắc chat 5 phút. Chỉ chỉnh tương tác/trình bày và công việc dựng giao diện phía trình duyệt.

**Điện thoại**:
- Menu và nút header có vùng bấm 44px, giữ nút sáng/tối ở 320px, hiển thị lối vào hồ sơ khi đăng nhập. Menu đồng bộ aria-expanded/controls, đóng bằng Escape/chạm ngoài/chọn link, không thêm tuyến hay thay menu.
- Ô nhập/select/textarea 16px và cao tối thiểu 44px; các nút chính đủ vùng chạm. Chữ mô tả tính cách 14px, giữ metadata riêng và thanh ngành mỏng đã duyệt. Giảm đệm hero hợp lý trên mobile, desktop giữ như trước.
- Nút AI nổi nhỏ khoảng 74px thay vì 221px, dùng cùng lối vào AI và nhãn truy cập; đặt theo safe-area. Khi đang làm bài trên mobile, ẩn nút nổi để không đè Câu tiếp theo; AI vẫn trong menu.
- Điều hướng bài trắc nghiệm hai cột, nút cao48px; ẩn gợi ý bàn phím trên thiết bị cảm ứng, giữ nguyên phím tắt/chọn đáp án/tính điểm.
- Modal giữ DOM/nội dung, có dialog semantics, Escape/focus trap/trả focus, khóa cuộn nền. Mobile giảm đệm lồng nhau và dùng phần nội dung cuộn riêng, nút đóng44px luôn thấy; mở lại bắt đầu từ đầu.

**Mượt hơn**:
- Dùng lại bản nhóm ngành vừa dựng cho listeners, bỏ 2 lượt gom nhóm thừa; giải phóng snapshot khi rời tra cứu.
- Gom các input tìm kiếm trong cùng khung hình bằng requestAnimationFrame, lấy trạng thái mới nhất, không làm mất focus; hủy/bỏ qua cập nhật khi reset/chuyển trang.
- Gom các token AI cho mỗi khung hình rồi dựng Markdown, vẫn tích lũy mọi token và flush cuối/lỗi/dừng. Kiểm tra phiên render trước chạm DOM; giữ vị trí khi người dùng cuộn đọc phía trên.
- Defer Lucide và marked để không chặn phân tích HTML; giữ Tailwind/config theo thứ tự cũ. Không thêm thư viện hay đổi cơ chế tải dữ liệu/API.

**Bản khôi phục**:
- Đã lưu đủ 6 file public/dist trước sửa ở backups/mobile-ux-20261115-baseline/before/, bản tối ưu ở after/ và SHA256 manifest.
- `python3 scripts/restore_mobile_20261115.py --check` kiểm tra; `--restore` hoàn tác 6 file. Công cụ từ chối nếu còn lock frontend, file/backup bị đổi hay có sửa khác về sau; không có force mặc định. Có cả hai snapshot để so sánh nếu cần giữ thay đổi mới.
- Fixture cách ly đã kiểm tra finalize một lần, toàn vẹn hai snapshot, từ chối backup hỏng/sửa về sau/lock, và restore đầy đủ. Không thử restore lên file thật. Snapshot tối ưu đã finalize và --check đạt.

**Kiểm tra**:
- ✅ Node syntax và 16 kiểm thử đăng nhập/trắc nghiệm, bộ lọc, chat-resume đạt; source/dist khớp. 60 tài sản minh họa gốc không đổi.
- ✅ Chrome giả lập cảm ứng 320/390/430px sáng/tối: home, danh sách quiz, tính cách, Bộ lọc, tra cứu ngành, login/register, so sánh, giới thiệu không tràn ngang; menu44px, theme còn ở320px, beacon nhỏ. Hồ sơ/intake và bốn quiz mở/chọn/chuyển câu vẫn hoạt động.
- ✅ Modal cuộn, nút đóng hiện, Escape và focus return; quiz controls hai cột và không bị nút nổi che. Xem ảnh home, modal và quiz. Tablet768/desktop1440 không tràn.
- ✅ Bộ lọc: 1 lượt gom nhóm mỗi render; 7 input liên tiếp chỉ 1 lượt dựng kết quả, tìm chính xác ngành không dấu, reset giữa input và rời route không có cập nhật cũ.
- ✅ AI dùng API/SSE giả lập, không ghi dữ liệu thử thật: 122 token thành đầy đủ câu trả lời với 2 lượt dựng nội dung (gồm placeholder), Markdown an toàn, Enter/Shift+Enter, năm, lỗi/gửi lại, stop, cuộn đọc, token cuối, chuyển route, sidebar/history/new chat.
- ✅ Hồi quy chat 5 phút bằng đồng hồ giả lập: mặc định mới, quay lại đúng hội thoại trong hạn, hết hạn mới, không ngắt người đọc lâu, mở lại tab, logout và tài khoản tách biệt.

**Lưu ý**: Đây là kiểm tra viewport/cảm ứng Chrome giả lập, chưa phải kiểm thử trực tiếp trên thiết bị iOS/Android thật. Không sửa cấu hình DB hoặc AI.

---

## [2026-11-15] Codex — Chat mới mặc định, tiếp tục hội thoại nếu quay lại trong 5 phút

**Files**: public/app.js, index.html và dist; tests/chat-resume.test.cjs. App 3.9.1, CSS giữ 2.9.4.

- Bỏ tự mở hội thoại mới nhất trong danh sách lịch sử. Chỉ tự mở đúng ID vừa rời nếu quay lại trước 300000ms và ID còn trong danh sách của tài khoản; hết hạn/ID thiếu/không có bản ghi thì hiện chat mới, không tự tạo phiên server trước khi gửi tin.
- Ghi thời điểm rời trang AI, chuyển tab ẩn hoặc pagehide; quay lại trang/tab/pageshow kiểm tra hạn. Không ngắt người vẫn đang đọc/chat sau 5 phút. Một lần rời chỉ ghi mốc đầu tiên, không kéo dài hạn do sự kiện lặp.
- Bản ghi localStorage theo user_id chỉ chứa ID hội thoại và thời điểm rời, hỗ trợ mở lại tab. Hết hạn/đăng xuất/nút Trò chuyện mới sẽ xóa; giữ lịch sử server. Không lưu nội dung tin nhắn trong bản ghi này. Bỏ con trỏ sessionStorage active cũ không có hạn.
- Giữ kiểm tra tài khoản/token/phiên render trước cập nhật async; cleanup listener khi đổi trang. Lựa chọn Trò chuyện mới/gửi tin trong khi tải lịch sử không bị ghi đè bởi việc khôi phục cũ. Link kèm câu hỏi vẫn mở hội thoại mới.

**Kiểm tra**:
- ✅ Node syntax; 3 kiểm thử resume (ranh giới 299999/300000ms, mặc định/legacy/dữ liệu lỗi/thời gian tương lai và phân tách tài khoản) cùng 4 kiểm thử quiz-auth đạt.
- ✅ Chrome với đồng hồ/API lịch sử giả lập, không ghi hội thoại thật: lần mở đầu mới dù có lịch sử; quay lại 1 phút khôi phục đúng hội thoại đã chọn, không lấy mới nhất; ở trong chat lâu không reset; rời quá 5 phút mở mới, lịch sử giữ nguyên.
- ✅ New chat vẫn mới khi quay lại nhanh; chuyển tab dưới/quá hạn; pagehide mô phỏng tải lại và môi trường lưu trữ tab mới; tài khoản khác không khôi phục nhầm; logout xóa bản ghi.
- ✅ public/dist khớp, website cổng 8000 đang phục vụ App 3.9.1. Không sửa backend hay thuật toán AI.

---

## [2026-11-15] Codex — Khôi phục chiều dài, giảm chiều cao thanh ngành

Người dùng xác nhận muốn thanh mỏng hơn theo CHIỀU CAO, không rút ngắn chiều dài. Hoàn tác giới hạn 800px ở summary và việc tách khung nội dung của lượt trước; trả thanh/details về toàn chiều dài ban đầu, viền/nền/hover trên details như cũ. Giảm summary min-height từ 82px xuống 64px, padding trên/dưới từ 16px xuống 8px; line-height tiêu đề/phụ 1.5 và cách dòng 3px. Giữ cỡ chữ, dòng trường/chương trình thụt và tự tăng chiều cao khi tên dài xuống dòng trên điện thoại. CSS 2.9.4; sync public/dist. Chrome 1440/390/320px sáng/tối: thanh tên ngắn cao64px, chiều dài khôi phục, không tràn, mở chi tiết hoạt động; xem ảnh desktop sáng.

---

## [2026-11-15] Codex — Khôi phục khung ngoài, chỉ thu thanh chứa tên ngành

Theo đính chính của người dùng: hoàn tác giới hạn 920px của khung kết quả, giới hạn tiêu đề/phân trang và danh sách 800px/căn giữa ở lượt trước; trở về bố cục ngoài rộng, đệm 24px và khoảng cách 12px. Chỉ summary (thanh chứa tên ngành) có chiều rộng tối đa 800px; chuyển nền/viền/bo góc/hover từ details sang summary. Khi mở, phần điểm/học phí là khối rộng đầy đủ bên dưới, không bị giới hạn theo thanh tiêu đề. Giữ phân cấp tên ngành và dòng trường/chương trình đã thụt. CSS 2.9.3, sync public/dist. Chrome 1440/390/320px sáng/tối: không tràn, tên chính/phụ rõ; khung ngoài >1000px, summary ≤800px, bảng mở >950px tại viewport1440. Đã xem ảnh desktop sáng; website HTTP 200.

---

## [2026-11-15] Codex — Thu gọn thanh ngành, căn giữa danh sách

Giới hạn khối kết quả ngành ở 920px, thanh ngành/tiêu đề/phân trang tối đa 800px và căn giữa. Tăng khoảng cách giữa thanh lên 14px, đệm ngoài 28px; giữ phân cấp tên ngành và số trường/chương trình đã thụt. Trên mobile tự co theo màn hình và giữ đệm 16px. Không sửa JS/dữ liệu. CSS 2.9.2, sync public/dist. Chrome 1440/768/390/320px sáng/tối đạt: thanh thu gọn, căn giữa, không tràn, mở bảng chi tiết hoạt động; xem ảnh desktop sáng.

---

## [2026-11-15] Codex — Phân cấp tên ngành và thông tin trường/chương trình

Sửa CSS khối ngành ở trang tra cứu: tên ngành tăng lên 16px (mobile 15px), giữ đậm; dòng số trường/chương trình nhỏ hơn, màu muted và thụt thêm 12px so với tên ngành (padding 31px tính cả mũi tên). Tăng nhẹ khoảng cách dòng/đệm để đọc rõ nội dung chính và phụ. Không đổi dữ liệu hay thao tác mở bảng. CSS 2.9.1, index/public-dist đồng bộ. Chrome 1440/390/320px sáng/tối xác nhận thụt dòng đúng, không tràn ngang và vẫn mở được chi tiết; đã xem ảnh desktop sáng. Website HTTP 200.

---

## [2026-11-15] Codex — Giao diện AI thoáng, lời chào và ô nhập ở giữa

**Files**: public/app.js, styles.css, index.html và dist. App 3.9.0, CSS 2.9.0.

**Thay đổi**:
- Màn hình bắt đầu lấy cảm hứng từ ảnh Google người dùng gửi: nền thoáng, lời chào theo tên tài khoản đã escape, tiêu đề rõ, một composer bo tròn ở giữa và ba gợi ý ngành/trường/học phí. Dùng màu navy/azure của website; không thêm nút chức năng chưa hỗ trợ.
- Khi có tin nhắn, chuyển cùng composer xuống dưới; AI trả lời trên nền thoáng, tin của người dùng có nền nhẹ. Chỉ một textarea/form, tự tăng chiều cao tối đa 160px; gợi ý và nút Hỏi chi tiết ngành điền bản nháp, không tự gửi.
- Lịch sử đóng mặc định; giữ drawer di động, backdrop/Escape, focus trap, inert, lịch sử theo tài khoản và phục hồi hội thoại. Toolbar gọn với lịch sử và trò chuyện mới.
- Giữ chọn năm, Enter gửi/Shift+Enter xuống dòng, trạng thái lỗi, dừng phản hồi, Markdown an toàn, bảng gợi ý nguyện vọng. Send/Stop đổi theo trạng thái, send tắt khi bản nháp trống. Gộp CSS chat cũ thành một khối để tránh các lớp override chồng nhau.
- Thẻ danh mục ngành co vừa màn hình 320px. Không sửa backend, luồng dữ liệu hoặc thuật toán AI.

**Kiểm tra**:
- ✅ Node syntax, source/dist khớp. Chrome dùng API/SSE giả lập, không ghi hội thoại thử vào tài khoản thật.
- ✅ Trạng thái bắt đầu: 1440×900, 1280×720, 768×900, 390×844, 320×680, 390×480 sáng/tối, không tràn ngang/trang ngoài, composer luôn nằm trong màn hình.
- ✅ Gợi ý điền bản nháp, textarea nhiều dòng, Shift+Enter, lỗi tạo phiên rồi gửi lại, stream Markdown và lọc HTML, năm 2027, send/stop, new chat, chọn lịch sử, phục hồi khi mở lại route, mặc định đóng lịch sử. Drawer desktop/mobile, backdrop/Escape/focus đạt.
- ✅ Xem ảnh desktop/light, mobile/dark và hội thoại; chỉnh icon trang trí không xuất hiện trên mobile để lời chào không cắt. Bảng portfolio responsive và Hỏi chi tiết vẫn điền đúng bản nháp.
- ✅ Cổng 8000 không chạy lúc kiểm tra; đã khởi động lại uvicorn ở apps/api, phiên exec 76854, PID 1478901. Website/DB healthy, đang phục vụ App 3.9.0 / CSS 2.9.0. Không khởi động hay sửa dịch vụ AI bên ngoài.

---

## [2026-11-15] Codex — Thay ba câu mô tả trên trang chủ

Thay nguyên văn mô tả Khám phá điểm mạnh, Khám phá sở thích và Định hướng nghề nghiệp theo nội dung người dùng cung cấp. Giữ bố cục và các nội dung khác. App 3.8.9, Node syntax đạt; sync public/dist.

---

## [2026-11-15] Codex — Bỏ emoji màu trùng với icon nét vẽ trong chi tiết tính cách

Bỏ emoji sao/cảnh báo/bóng đèn và emoji trang trí mũ tốt nghiệp/lá trong tiêu đề MBTI và tổ hợp RIASEC, bao gồm tab từng trục và Xem tất cả. Giữ nguyên mọi icon Lucide nét vẽ, dấu danh sách, nội dung và hình minh họa. Không đổi badge Nổi bật của bài đánh giá năng lực. App 3.8.8; kiểm tra Node syntax và số định nghĩa icon Lucide trước/sau khớp; sync public/dist.

---

## [2026-11-15] Codex — Bỏ dòng Xem chi tiết dưới nhóm tính cách

Bỏ dòng hành động và mũi tên dưới các nhóm MBTI/RIASEC trong gallery chung trang chủ/trang Nhóm tính cách. Giữ nguyên nhấn ảnh/mô tả và Enter/Space để mở thông tin; giữ nhãn truy cập. App 3.8.7; Node syntax đạt, đồng bộ public/dist.

---

## [2026-11-15] Codex — Chữ tính cách không khung, bỏ tên lặp và tối ưu tải nhẹ

**Files**: public/app.js, styles.css, index.html và dist. App 3.8.6, CSS 2.8.1.

**Giao diện**:
- RenderTypeGridContent dùng chung cho trang Nhóm tính cách và trang chủ: bỏ nền/viền/bóng ô mô tả và đường chia CTA, căn giữa câu giới thiệu/mô tả/liên kết để chữ đứng trực tiếp trên nền trang. Hiện đủ câu thay vì cắt dòng MBTI.
- Tên đã có trong SVG không lặp lại bằng heading nhìn thấy bên dưới; giữ heading sr-only và thêm tên truy cập cho thao tác bàn phím/đọc màn hình. Bỏ badge mã bị trùng với mã trong ảnh. Giữ ảnh lớn và thứ tự/tab/chi tiết cũ.
- Mềm viền sáng hỗ trợ chữ có sẵn trong SVG trên dark theme; không thay đổi các file ảnh.

**Tối ưu không đổi cấu trúc ứng dụng**:
- Chín fetch JSON tĩnh chuyển từ URL timestamp mới mỗi lượt sang URL ổn định với cache:no-cache để trình duyệt kiểm tra file mới và dùng lại body đã lưu khi máy chủ trả 304. Không thêm lưu dữ liệu tài khoản, không cache API động; giữ Promise.all và cấu trúc state như cũ.
- Ảnh hàng đầu eager, phần còn lại lazy và decoding async; ảnh tổ hợp RIASEC cũng lazy/async, khai báo đúng kích thước gốc 400x440.
- Bỏ drop-shadow/filter thay đổi theo hover trên ảnh lớn; chỉ chuyển động transform nhẹ, tôn trọng reduced-motion. Không thêm thư viện, không sửa backend/AI/chấm điểm.

**Kiểm tra**:
- ✅ Node syntax và source/dist khớp. Hash 60 tài sản minh họa trước/sau không đổi; máy chủ website healthy.
- ✅ Chrome MBTI/RIASEC ở 1440/1024/768/390/320px sáng/tối: không khung chữ, không lặp tiêu đề nhìn thấy, không che chữ hoặc tràn ngang. Enter mở đúng chi tiết; trang chủ dùng cùng gallery vẫn hoạt động.
- ✅ Tải lại trong Chrome: cả 9 JSON tĩnh nhận HTTP 304, không tải lại body. Dữ liệu vẫn đủ 4 bài, 16 MBTI, 6 RIASEC, 126 trường và 3478 chương trình.
- ✅ Xem ảnh desktop sáng và mobile tối; kiểm tra ảnh cuối sau làm mềm nền sáng cho chữ SVG.

---

## [2026-11-15] Codex — Minh họa tính cách lớn, nhô khỏi thẻ

**Files**: public/app.js, styles.css, index.html và dist. App 3.8.5, CSS 2.8.0.

- Bố cục chung renderTypeGridContent (trang Nhóm tính cách và trang chủ) cho 16 MBTI, 6 RIASEC: bỏ khung gradient/cắt ảnh, thay bằng vùng minh họa trong suốt với overflow visible, ảnh lớn tối đa 280px/300px nhô lên trên và chồng nhẹ lên ô mô tả riêng bên dưới. Thêm khoảng cách hàng để không đè chữ, giữ badge và nội dung cũ.
- Hover ảnh nâng nhẹ; CSS chuyển động thêm tuân thủ reduced-motion. Thẻ hỗ trợ Enter/Space và focus bàn phím. Nền sáng mờ nhỏ phía sau phần chữ có sẵn trong ảnh giúp đọc được trên dark theme.
- Không thay đổi file ảnh, SVG, ảnh fallback hoặc nội dung/thuật toán trắc nghiệm. Hash 60 tài sản personality/riasec animated trước và sau khớp.

**Kiểm tra**: Node syntax, public/dist khớp; Chrome cả MBTI/RIASEC ở 1440/1024/768/390/320px sáng/tối: ảnh tải được, tràn vùng minh họa như thiết kế, không tràn ngang; mở chi tiết và trang chủ hoạt động. Xem ảnh desktop sáng/tối và mobile tối; máy chủ website healthy.

---

## [2026-11-15] Codex — Giới thiệu đủ bốn bài và ưu tiên RIASEC, năng lực nhận thức

Sửa bước Chọn bài test và FAQ trang chủ để giới thiệu đủ bốn bài, khuyến khích RIASEC và Đánh giá năng lực nhận thức trước. Danh sách thẻ dùng thứ tự RIASEC, cognitive, Big Five, MBTI cho cả dữ liệu tải về và fallback, không sửa mảng nguồn hay thuật toán chấm điểm. App 3.8.4; kiểm tra Node syntax, đồng bộ public/dist.

---

## [2026-11-15] Codex — Tiêu đề khối chỉ hiển thị tên ngành

Bỏ mã đại diện và số lượng mã khỏi header khối ngành; giữ tên ngành, số trường/chương trình, dáng bo tròn và hiệu ứng hover. Mã từng chương trình trong bảng chi tiết vẫn giữ để đối chiếu dữ liệu. Sửa public/app.js, index.html (App 3.8.3), đồng bộ dist; kiểm tra Node syntax đạt.

---

## [2026-11-15] Codex — Khối ngành bo tròn theo ảnh mẫu và chuyển động hover

**Files**: public/app.js, styles.css, index.html và dist. App 3.8.2, CSS 2.7.2.

- Đổi header khối ngành thành dạng bo tròn dài, cao tối thiểu 76px, mũi tên tam giác bên trái, mã · tên ngành cùng dòng; bỏ ô chữ cái và nhãn hành động bên phải. Dòng phụ hiển thị số trường/chương trình và số mã khi có nhiều mã.
- Mã đại diện lấy từ mã xuất hiện nhiều nhất trong các dòng đang lọc; bảng mở vẫn giữ đầy đủ mã/điểm/học phí riêng của từng chương trình. Dữ liệu workbook hiện tại không có tổ hợp môn để điền như ảnh mẫu, không tự suy đoán.
- Hover trên máy có chuột: nâng 3px, đổi nền/viền, bóng nhẹ, transition 220ms; rời chuột trở lại. Khi mở, mũi tên xoay và nội dung xuất hiện nhẹ. Tôn trọng prefers-reduced-motion; vẫn dùng details/summary hỗ trợ bàn phím.
- Giữ nguyên các bộ lọc, phân trang, dữ liệu và backend AI.

**Kiểm tra**: Node syntax và 9 kiểm thử bộ lọc đạt; source/dist đồng bộ. Chrome mở/đóng và không tràn ngang ở 1440/390/320px sáng/tối; xem ảnh desktop/light và mobile/dark. Chrome với con trỏ desktop kiểm tra computed transform -3px khi hover, trở về none khi rời chuột và không dịch chuyển khi reduced-motion. Máy chủ website healthy.

---

## [2026-11-15] Codex — Khối ngành đóng/mở để xem điểm và học phí

**Files**: public/app.js, styles.css, index.html và dist; tests/university-filters.test.cjs. App 3.8.1, CSS 2.7.1.

**Thay đổi**:
- Trong mục Tra cứu ngành & điểm của từng trường (#tra-cuu-nganh) thuộc Bộ lọc, thay bảng trải sẵn bằng một khối đóng/mở cho mỗi tên ngành đã chuẩn hóa. Tiêu đề khối hiển thị số trường và số chương trình, có nhãn Điểm & học phí trên desktop.
- Nhấn/Enter vào ngành mới tạo bảng so sánh điểm theo từng phương thức và học phí theo trường. Nhấn lại để thu gọn; mở khối khác đóng khối trước. Tất cả khối mặc định đóng, giữ nguyên bộ lọc không dấu/tỉnh thành/phương thức.
- Phân trang danh sách 12 ngành/trang và bảng trong ngành 20 chương trình/trang, không gộp điểm giữa các mã/chương trình. Giữ nhãn phân biệt học phí riêng và khoảng cấp trường; không đổi dữ liệu nguồn hay backend AI.
- Layout desktop/mobile, màu theo theme, focus bàn phím và reduced-motion.

**Kiểm tra**:
- ✅ Node syntax; 9 kiểm thử bộ lọc đạt, gồm gom đúng và đủ toàn bộ chương trình, không trùng khối, mặc định đóng, phân trang, trạng thái rỗng và dữ liệu nguồn giữ nguyên.
- ✅ Chrome: mở/đóng, xem điểm/học phí, phân trang trong ngành và danh sách, bộ lọc phương thức, Enter mở khối, chỉ một khối mở.
- ✅ 1440/390/320px sáng/tối: cả đóng/mở không tràn ngang; xem ảnh desktop/sáng và mobile/tối. Máy chủ hiện tại hoạt động, source/dist đồng bộ.

---

## [2026-11-15] Codex — Gộp ngành trong bộ lọc và bảng tra cứu ngành liên trường

**Files**: public/app.js, styles.css, index.html và dist; tests/university-filters.test.cjs. App 3.8.0, CSS 2.7.0.

**Thay đổi**:
- Canonical danh sách gợi ý ngành theo tên đã làm sạch STT đầu dòng `(1)`/`1.`, dấu sao/chú thích `(*)`, khoảng trắng và key không dấu/không phân biệt hoa thường, dấu câu; `&` tương đương “và”. Chọn nhãn đại diện xuất hiện nhiều nhất. Giữ số có nghĩa như 2+2/Quân khu 4 và hậu tố chương trình/chuyên ngành. Không sửa tên gốc trong workbook/JSON/DB.
- Khi tên đầy đủ khớp một mục canonical, lọc đúng key đó, không kéo theo tên ngành dài hơn; mã ngành đầy đủ cũng khớp chính xác. Khi gõ dở vẫn tìm/gợi ý theo một phần tên. Kết hợp ngành/phương thức/THPT kiểm tra trên chương trình liên quan, không lấy điểm của ngành khác trong trường để đáp ứng bộ lọc.
- Thẻ trường hiển thị ngành đang lọc và số chương trình khớp; khoảng THPT của ngành lấy đúng admissions của những chương trình đó.
- Làm nổi bật CTA “Tra cứu ngành & điểm của từng trường” trong Bộ lọc bằng nền navy, chữ trắng, icon và bóng; chuyển tới route #tra-cuu-nganh, giữ các bộ lọc đang chọn, menu Bộ lọc vẫn active.
- Bảng mới gồm trường/địa danh, tên chương trình, mã, loại chương trình, điểm raw tách theo phương thức/thang, và học phí. Giá chương trình chỉ dùng nếu có, còn lại ghi rõ khoảng học phí cấp trường. Không điền giá/điểm thiếu. Có nguồn/chi tiết, 20 chương trình mỗi trang; mobile chuyển hàng thành thẻ.

**Kiểm tra**:
- ✅ 8 kiểm thử bộ lọc bằng Node (5 cũ + 3 canonical/exact lookup) và kiểm thử auth đạt; syntax/source-dist khớp.
- ✅ Chrome: tên gợi ý không còn STT, nhập không dấu, mở CTA, bảng chỉ có ngành đã chọn, phân trang, đổi phương thức reset trang và chỉ hiển thị phương thức đó.
- ✅ 1440/390/320px light/dark không tràn ngang; đã xem ảnh bảng desktop/light và mobile/dark. Giữ nguyên dữ liệu 126 trường/3478 chương trình.

**Lưu ý**: Các chương trình khác mã/loại vẫn là các hàng riêng trong bảng dù cùng ngành; đây là biến thể tuyển sinh trong file, không xóa/gộp điểm giữa các chương trình. Các hậu tố chuyên ngành/loại chương trình vẫn được giữ để tránh gộp nhầm những lựa chọn khác nhau.

---

## [2026-11-15] Codex — Đổi nhãn nút khám phá nhóm tính cách

Đổi riêng nút trang chủ từ “Khám phá 16 nhóm” thành “Khám phá nhóm tính cách”; giữ liên kết #nhom-tinh-cach. Sửa public/app.js, bump App 3.7.4 trong index.html và sync dist. Kiểm tra Node syntax và source/dist khớp.

---

## [2026-11-15] Codex — Điều chỉnh cách viết nhãn Bộ lọc

Đổi “Bộ Lọc” thành “Bộ lọc” ở menu desktop, mobile và footer trong public/index.html; sync dist/index.html. Giữ nguyên route và chức năng. Đã kiểm tra đủ ba nhãn và public/dist khớp.

---

## [2026-11-15] Codex — Giới thiệu đủ bốn bài trắc nghiệm và nhãn Bộ Lọc

- Sửa Phương pháp và “Ba khung” thành “Bốn bài trắc nghiệm, một hồ sơ”; bổ sung Năng lực nhận thức (ngôn ngữ, định lượng, hình ảnh/quy luật), bỏ cụm “không phải hộp nghề”.
- Đổi nhãn liên kết Hướng nghiệp thành Bộ Lọc ở menu desktop, mobile và footer, giữ nguyên route #huong-nghiep.
- Files: public/app.js, index.html và dist; App 3.7.3. Kiểm tra Node syntax, đủ bốn mục trong renderAbout và nhãn điều hướng, source/dist khớp.

---

## [2026-11-15] Codex — Lịch sử chat luôn đóng mặc định

Theo yêu cầu mới: bỏ ghi nhớ trạng thái mở sidebar. Mỗi lần mở/tải lại trang chat và khi đổi breakpoint desktop/mobile, lịch sử đều đóng; chỉ mở khi người dùng nhấn nút Lịch sử. Giữ nguyên dữ liệu hội thoại và chức năng mở/đóng, backdrop/Escape.

Files: public/app.js, index.html và bản dist; App 3.7.2. Kiểm tra Node syntax và public/dist khớp.

---

## [2026-11-15] Codex — Chat rộng toàn màn hình và ngăn lịch sử đóng/mở

**Files**: public/app.js, styles.css, index.html và bản dist. App 3.7.1, CSS 2.6.1.

**Thay đổi**:
- Chat chiếm phần chiều cao còn lại sau header, không tạo thanh cuộn trang ngoài. Khung tin nhắn cuộn riêng, ô nhập luôn ở dưới; gọn tiêu đề/composer và tăng cỡ chữ/khoảng dòng nội dung.
- Bỏ giới hạn khung 1440/đệm lớn quanh tin nhắn; assistant rộng tối đa 1200px, user theo độ dài nội dung. Sidebar desktop rộng 280px có nút đóng/mở, ghi nhớ theo tài khoản trong localStorage; đóng sidebar trả lại chiều rộng cho chat.
- Mobile dùng drawer phủ một phần màn hình, backdrop, nút ×, Escape, focus trap và inert phần chat khi mở. Khôi phục focus khi đóng, đồng bộ aria-expanded/aria-controls; thay đổi breakpoint có listener cleanup để tránh tích lũy.
- Có nút tạo cuộc trò chuyện mới trên thanh tiêu đề để dùng ngay khi sidebar đóng. Lịch sử/tin nhắn/API lưu trữ giữ nguyên.

**Kiểm tra**:
- ✅ Node syntax, kiểm thử auth/filter và public/dist khớp.
- ✅ Chrome mock API: gửi/stream/Markdown an toàn/new chat/mở lịch sử/reload vẫn đạt. Desktop đóng sidebar tăng chiều rộng >200px và nhớ trạng thái sau render lại. Mobile backdrop/Escape/khôi phục focus đạt.
- ✅ 1440/390/320px light/dark không tràn ngang, không cuộn toàn trang ngoài ý muốn, composer nằm trong viewport. Đã xem ảnh desktop/light và mobile/dark.

---

## [2026-11-15] Codex — Thay trang tư vấn bằng giao diện chat và lịch sử theo tài khoản

**Files chính**:
- `apps/web/public/app.js`, styles.css, index.html và bản dist — Bỏ form/pipeline kỹ thuật, dùng sidebar hội thoại, bong bóng tin nhắn, composer ở dưới, Enter gửi/Shift+Enter xuống dòng, nút dừng, cuộc trò chuyện mới; ghi nhớ thread đang mở theo tài khoản trong sessionStorage. Lịch sử và nội dung lấy từ API/database, không lưu toàn bộ chat ở localStorage. Render Markdown đã escape HTML, giới hạn tag/attribute và giao thức link; phân tách SSE qua nhiều chunk, xử lý UTF-8 và DONE. Guard account/view để không ghi nội dung vào trang/tài khoản khác khi điều hướng. Mobile có nút Lịch sử, ẩn footer và nút AI nổi riêng tại trang chat.
- `apps/api/app/modules/consultation/history_router.py`, history_migration.py — API /api/v1/chat/sessions: list/create/read messages/stream. Xác minh chủ hội thoại mọi lần đọc/ghi. Lưu user và assistant vào DB, giữ phản hồi từng phần khi ngắt stream; lời chào không cần hồ sơ. Các lỗi thiếu hồ sơ/RIASec trả thành tin nhắn hướng dẫn, không giả lập điểm.
- `apps/api/app/core/models_db.py`, database.py, main.py — Thêm chat_sessions.owner_user_id nullable FK users, index và migration backfill từ student_id, hỗ trợ admin không có student profile. Migration chạy idempotent trong init_db; đã ghi kế hoạch schema trước khi áp dụng.
- `apps/api/app/modules/graphrag/models/recommendation.py`, router.py, profile_context.py — Chuyển lịch sử gần nhất cho báo cáo; dùng câu hỏi mới ưu tiên từng slot, lấy thông tin còn thiếu từ các lượt user trước rồi mới hồ sơ; không dùng điểm trong câu trả lời assistant làm điểm học sinh. Giữ nguyên lọc tất định và model/provider AI hiện có.
- `apps/api/app/modules/consultation/service.py`, router.py — Kiểm tra ownership cho đọc tin nhắn và append session qua API cũ.
- `apps/api/tests/test_chat_history.py` — Kiểm thử lịch sử, privacy, admin, streaming/context, migration; tests auth/filter cũ vẫn đạt. App 3.7.0, CSS 2.6.0.

**Kết quả kiểm tra**:
- ✅ 7 kiểm thử chat bằng SQLite memory, 10 kiểm thử tư vấn, Node auth/filter và syntax đạt. Không ghi hội thoại mẫu vào database thật.
- ✅ Chrome với API giả: gửi/stream tin nhắn, Markdown an toàn (HTML hiển thị dạng chữ), cuộc trò chuyện mới, chọn lại lịch sử, tải lại route khôi phục thread; 1440/390/320px light/dark không tràn ngang, lịch sử mobile mở được. Đã xem screenshot desktop/light và mobile/dark.
- ✅ Xác minh migration PostgreSQL và backfill đã áp dụng, health ok và GET chat/sessions không đăng nhập trả 401.
- ✅ Xác nhận cổng 8000 lúc này chạy For Your Future từ apps/api; restart đúng tiến trình đó để nạp API mới, giữ cổng người dùng đang mở.

**Giới hạn**: Bộ nhớ hội thoại dùng 12 tin gần nhất (tối đa 6 lượt user để bổ sung slot); thông tin học sinh/điểm thiếu vẫn cần bổ sung. Lời chào là phản hồi cố định; tư vấn trường/ngành tiếp tục dùng dữ liệu lọc có căn cứ, không chuyển thành chatbot đa lĩnh vực.

---

## [2026-11-15] Codex — Đang triển khai chat và lịch sử theo tài khoản

Migration được chuẩn bị trước khi áp dụng: thêm chat_sessions.owner_user_id nullable tham chiếu users, index và backfill từ student_id. Giữ dữ liệu hội thoại cũ, hỗ trợ cả tài khoản admin không có hồ sơ học sinh. Không thay schema điểm/học phí.

---

## [2026-11-14] Codex — Hiệu ứng chuyển động nhẹ cho thẻ, menu và nút

**Files**: `apps/web/public/styles.css`, `index.html` và bản sync dist. CSS 2.5.3; không đổi app.js hoặc dữ liệu.

**Thay đổi**:
- Thẻ trường nâng 4px cùng bóng/viền khi dùng chuột; nút nâng 2px, menu và chip nâng 1px. Thời gian chuyển 180–260ms; nhấn nút thu nhẹ trong 80ms.
- Tiêu đề hero và thẻ tóm tắt hiện nhẹ, nội dung ngành mở có hiệu ứng ngắn 240ms; không chạy animation trên toàn bộ danh sách khi gõ tìm kiếm.
- Hiệu ứng hover chỉ dành cho `hover:hover` + `pointer:fine`; chế độ reduced-motion tắt animation/transition mới. Không thêm listener mousemove hoặc vòng lặp JS; hiệu ứng hoạt động theo theme.

**Kiểm tra**:
- ✅ Chrome headless mặc định báo pointer/hover không khả dụng: xác minh thẻ không bị nâng; mô phỏng riêng điều kiện fine-pointer qua media rule trong bộ nhớ kiểm thử thấy transform -4px.
- ✅ Emulation reduced-motion: transform none, transition 0s, animation mở ngành none; trở về no-preference có animation fyf-detail-enter.
- ✅ Mobile 390/320px light/dark không tràn ngang; source/dist khớp. Không ghi thay đổi mô phỏng media vào source.

---

## [2026-11-14] Codex — Nút hành động thẻ trường theo ảnh mẫu

- Chỉ chỉnh footer thẻ trường: CTA “Xem ngành & điểm” nền navy/chữ trắng, nút “Trang trường” viền và icon mở ngoài, liên kết “Trang tuyển sinh” kèm icon. Nút thiếu URL được ẩn, link ngoài có noopener/noreferrer; các link không kích hoạt click mở thẻ.
- Nút cao tối thiểu 44px, tự xuống hàng; màu theo light/dark. Ghi chú RIASEC chỉ hiện khi có kết quả thực.
- Files: public/app.js, styles.css, index.html và bản sync dist. App 3.6.3, CSS 2.5.2.
- ✅ Node syntax và bộ kiểm thử auth/filter đạt. Không đổi dữ liệu hoặc thiết kế các phần khác. Chưa kiểm tra trực quan lần chỉnh này trên Chrome.

---

## [2026-11-14] Codex — Khôi phục giao diện trước lần thêm điểm nhấn nền sáng

Theo yêu cầu người dùng, hoàn tác riêng lần thiết kế highlight vừa thực hiện: gỡ CSS light-theme mới, bỏ nhấn/gạch chân tiêu đề, khôi phục CTA/thẻ số liệu/học phí/THPT và menu/bộ lọc về giao diện trước. Giữ dữ liệu workbook mới, bộ lọc, trang trường và các sửa tương phản đã có trước đó.

**Files**: public/app.js, styles.css, index.html và bản sync dist; docs/TODO.md. App 3.6.2, CSS 2.5.1 để trình duyệt tải lại giao diện khôi phục.

**Kiểm tra**: Node syntax, kiểm thử auth/filter và source/dist khớp.

---

## [2026-11-14] Codex — Tăng phân cấp và điểm nhấn cho nền sáng

**Files đã thay đổi**:
- `apps/web/public/app.js`, `apps/web/dist/app.js` — Đánh dấu ngữ nghĩa hero/actions/metrics và hai thẻ học phí/THPT; nhấn cụm “Chọn đúng hướng đi” trong tiêu đề, không thay nội dung hoặc dữ liệu.
- `apps/web/public/styles.css`, `apps/web/dist/styles.css` — Chỉ áp dụng phần thiết kế mới dưới `:root:not(.dark)`: nền xanh xám tạo độ tách thẻ trắng, hero chuyển màu dịu, CTA chính đậm và CTA phụ viền, số liệu trang chủ có viền cyan, trạng thái menu/bộ lọc được chọn rõ hơn, nhãn đếm có nền; học phí vàng nhạt và THPT xanh nhạt; ngành mở rộng có thanh nhấn bên trái; tiêu đề báo cáo tư vấn có nền và vạch trái.
- `apps/web/public/index.html`, `apps/web/dist/index.html` — App 3.6.1, CSS 2.5.0.

**Kiểm tra**:
- ✅ Node syntax, bộ kiểm thử auth/filter và public/dist khớp.
- ✅ Chrome: xem ảnh trang chủ và trang trường desktop/light; kiểm tra trang trường 1440/390/320px cả hai theme không tràn ngang. Tìm ngành không dấu/lọc TSA/mở ngành hoạt động, HCMUT không hiện THPT cũ.
- ✅ Các cặp màu nhấn chính kiểm tra theo độ chói đạt >=4.5:1 (học phí 7.11, THPT 10.22, CTA 6.85, tiêu đề nhấn 6.23). Không tuyên bố chứng nhận tương phản toàn trang.
- Không thay backend, thuật toán AI, dữ liệu tuyển sinh hay cách lưu hồ sơ.

---

## [2026-11-14] Codex — Thay dữ liệu tuyển sinh bằng file Điểm và học phí.xlsx và thiết kế lại trang trường

**Nguồn**: File Drive do người dùng cung cấp `1cXuaWCjI-yxyXg3SpxKGaR3P51Rp8o50`, lưu tại `data/raw/diem_va_hoc_phi_2026_20261114.xlsx`; SHA256 và thống kê tại `data/staging/workbook_import_report.json`.

**Thay đổi**:
- `scripts/replace_admissions_workbook.py` — Import 126 sheet trường + 2 sheet rà soát; giữ nguyên tên ngành, tên phương thức, văn bản điểm/ghi chú, dòng Excel; đọc link từ HYPERLINK (kể cả dấu quote escape). Cột header số tiền của HCMUS/TDTU tách thành học phí từng dòng, không nhập thành điểm.
- `apps/web/public/data/` và bản dist/staging — Thay universities.json, school_details.json, thêm admissions_review.json. Chỉ dùng metadata cũ cho ID, địa danh và taxonomy RIASEC khi file không cung cấp; không ghép ngành/điểm/học phí cũ.
- `scripts/sync_workbook_database.py` — Thay dữ liệu 3 bảng universities/programs/admission_criteria theo giao dịch; nhập bulk, giá trị thiếu lưu NULL, giữ tài khoản/hồ sơ/trắc nghiệm. Có snapshot dự phòng không dùng hiển thị trong data/backups.
- `scripts/sync_workbook_graph.py` — Thay Program/AdmissionCriteria/FinancialAspect trong Neo4j của 126 trường. Chỉ giữ liên kết nghề/tổ hợp phụ trợ khi trường+mã+tên khớp chính xác, không suy đoán cho ngành mới. Đã ghi 3.478 Program, 11.428 criteria; 839 chương trình còn đầy đủ context nghề+tổ hợp cũ.
- `apps/api/app/modules/universities/schemas.py`, `service.py` — Hỗ trợ thông tin học phí/thời lượng/văn bằng trống; trả raw_score và scale gốc, không tự gán điểm quy đổi thành điểm gốc.
- `apps/api/app/modules/graphrag/query_builder.py`, `models/query_builder.py`, `profile_context.py` — Luồng tư vấn THPT chỉ dùng phương thức THPT riêng /30; ghi chú học phí cấp trường dùng cận trên khi chưa có giá chương trình.
- `apps/web/public/app.js`, styles.css, index.html và dist — Trang trường mới theo design system: hero, học phí và nguồn, điểm THPT riêng, tìm ngành không dấu, dropdown phương thức thực của trường, từng ngành mở rộng để xem nguyên văn điểm và thang điểm; thay bảng cố định gộp /100 và /1200. App 3.6.0, CSS 2.4.0.
- `tests/test_workbook_catalog.py`, `tests/university-filters.test.cjs` — Đối chiếu toàn bộ chương trình/ô dữ liệu với workbook, kiểm tra bỏ điểm THPT cũ, thang điểm, filter theo nhãn phương thức mới.

**Kiểm tra**:
- ✅ 126 trường, 3.478 chương trình, 11.428 ô phương thức/điểm khớp Excel, SQL và graph. 21 trường không có cột THPT riêng không còn dùng THPT cũ.
- ✅ 3 kiểm thử workbook và 10 kiểm thử tư vấn backend đạt; kiểm thử Node auth/filter và syntax đạt; public/dist khớp.
- ✅ Chrome desktop 1440px, mobile 390/320px cả light/dark: trang HUST, tìm không dấu, phương thức TSA, giữ raw 45,62/100; HCMUT không hiện THPT riêng; không tràn ngang. Đã xem ảnh chụp mobile.
- ✅ Chạy lại For Your Future cổng 8001, health ok; không đổi connection string hay mô hình AI.

**Lưu ý**:
- Học phí cấp trường không được gán thành học phí chính xác của từng ngành trong SQL/UI. Graph dùng giá từng dòng nếu có, nếu không dùng cận trên của khoảng học phí trường và ghi rõ trong context.
- Chương trình chưa có đủ liên kết nghề/tổ hợp chưa được đưa vào tư vấn graph; dữ liệu tra cứu vẫn đầy đủ. Không tự tạo tổ hợp/điều kiện sơ tuyển không có trong file.
- Không chạy lại importer staging cũ để ghi đè dữ liệu mới; dùng ba script workbook trên theo thứ tự extract → database → graph.

---

## [2026-11-13] Codex — Bộ lọc trường theo mẫu, tìm ngành và địa danh không dấu

**Files đã thay đổi**:
- `apps/web/public/app.js`, `apps/web/dist/app.js` — Panel bộ lọc gồm miền, tỉnh phổ biến, tỉnh/TP mới/cũ, học phí, điểm THPT, mức phù hợp RIASEC, nhóm ngành, ngành và phương thức. Tìm trường/ngành/mã ngành/tỉnh cũ/mới không dấu bằng chuẩn hóa Unicode và đ/Đ; chỉ mục WeakMap. Gợi ý ngành lọc theo nội dung nhập không dấu. Đếm kết quả, trạng thái rỗng, xóa bộ lọc; cập nhật riêng danh sách khi gõ, giữ con trỏ và không nhân đôi panel/listeners.
- `apps/web/public/styles.css`, `apps/web/dist/styles.css` — Panel/chip/input theo theme, control >=40px/44px mobile; 2 cột desktop, 1 cột mobile; sửa grid danh sách có tên trường dài gây tràn ngang.
- `apps/web/public/index.html`, `apps/web/dist/index.html` — App 3.5.6, CSS 2.3.4.
- `tests/university-filters.test.cjs` — Kiểm thử dữ liệu thực và biên lọc; `docs/TODO.md` — Ghi nhận hoàn thành.

**Kết quả**:
- ✅ Kiểm thử Node: tên trường/ngành/tỉnh có dấu và không dấu, Bình Dương cũ ↔ TP.HCM mới, Hải Dương cũ ↔ Hải Phòng mới, ngành/mã, học phí (phân biệt 0 với thiếu dữ liệu), điểm THPT, phương thức, RIASEC, escape HTML.
- ✅ Chrome với dữ liệu local: gõ không mất focus, chỉ một panel/grid, lọc tỉnh cũ trả 3 trường Bình Dương, gợi ý ngành không dấu, reset về 126 trường. Không tràn ngang ở 1440/390/320px cả light/dark; đã xem ảnh desktop/light và mobile/dark.
- ✅ Node syntax và public/dist khớp. Không thay backend/AI hay sửa dữ liệu địa danh.

**Lưu ý**:
- Tỉnh mới/cũ dùng đúng hai trường provinceNew/provinceOld của dataset, không tự suy luận sáp nhập.
- Học phí dùng khoảng đã có trong school_details, fallback metadata khi có; không suy đoán trường thiếu học phí. THPT chỉ lấy admissions2026.thptValues hợp lệ /30, không trộn điểm sàn/ĐGNL.
- Nhóm ngành dùng logic category/focusRiasec kế thừa frontend gốc. RIASEC fit dùng cosine cùng trọng số của src/lib/riasec.ts; chưa có kết quả thì vô hiệu hóa ngưỡng fit, không gán phần trăm giả.

---

## [2026-11-13] Codex — Mở đúng website khi cổng 8000 đang chạy GraphRAG riêng

**Kết quả**:
- Xác nhận cổng 8000 đang chạy `python3 app/backend/main.py` từ `/home/labsit/GraphRAG`, root trả JSON giới thiệu API.
- Giữ nguyên tiến trình GraphRAG, chạy For Your Future từ `apps/api` trên `0.0.0.0:8001`.
- ✅ HTTP xác minh trang chủ có SPA app-container, CSS theme version 2.3.3 và `/health` trả ok.
- Địa chỉ truy cập theo IP người dùng đang sử dụng: `http://100.64.1.2:8001/`. Chưa xác minh kết nối từ thiết bị của người dùng.
- Không thay đổi code ứng dụng hoặc file ngoài for-your-future. Script start.sh mặc định vẫn dùng 8000; cần đảm bảo cổng trống hoặc chỉ định 8001 khi chạy cùng GraphRAG riêng.

---

## [2026-11-13] Codex — Cải thiện độ tương phản nền tối và nền sáng

**Files đã thay đổi**:
- `apps/web/public/styles.css`, `apps/web/dist/styles.css` — Tách màu chữ tiêu đề khỏi nền thương hiệu; thay hàng trăm dòng override dark bằng quy tắc theo bề mặt/ngữ cảnh. Bỏ ép mọi heading/strong/số sang trắng; CTA nền đậm và chữ sáng ổn định cả hover; badge xanh/vàng/tím/đỏ có màu theo theme.
- `apps/web/public/index.html`, `apps/web/dist/index.html` — CSS version 2.3.3.
- `docs/TODO.md` — Ghi nhận cải thiện giao diện.

**Kết quả**:
- ✅ Chữ phụ, cyan, thông báo thành công/cảnh báo/lỗi ở nền sáng đậm hơn; ô mật khẩu, input/select/textarea, placeholder, autofill, focus và native color-scheme theo theme.
- ✅ Sửa tiêu đề trên nền navy bị chìm ở nền sáng; bổ sung nền color-mix cho các class opacity dùng CSS variable (đặc biệt thẻ hồ sơ mẫu trên ảnh và header).
- ✅ Chrome headless: đã kiểm tra và xem ảnh chụp nền sáng/tối; quét các trang home/login/register/quiz/personality/university/comparison/profile/consultation cùng chi tiết trường và kết quả RIASEC với dữ liệu mẫu. Phép đo tự động giới hạn chữ trên nền phẳng; gradient/ảnh kiểm tra trực quan, không tuyên bố chứng nhận WCAG toàn trang.
- ✅ Các cặp màu chữ nhỏ chủ đạo đạt tỷ lệ >=4.5:1 khi tính theo công thức độ chói; Node syntax và source/dist khớp.

**Lưu ý**:
- Chỉ sửa giao diện trong for-your-future, không sửa logic AI/dữ liệu.
- Cổng 8000 tại lúc kiểm tra đang phục vụ GraphRAG API riêng; kiểm tra UI qua máy chủ static tạm để không ảnh hưởng dịch vụ đó.

---

## [2026-11-13] Codex — Kết nối hồ sơ và trắc nghiệm vào tư vấn trong for-your-future

**Phạm vi**: Chỉ thay đổi trong `/home/labsit/for-your-future/`; không sửa repo GraphRAG bên ngoài, cấu hình DB hoặc mô hình/provider AI.

**Files đã thay đổi**:
- `apps/web/public/app.js` và `dist/app.js` — Gửi JWT khi tư vấn; đồng bộ RIASEC/MBTI/Big Five qua API personality, cognitive qua API competency. Hàng đợi kết quả lỗi tách theo user_id và thử lại trước tư vấn; tải kết quả personality của tài khoản khi đăng nhập, xóa cache hiển thị giữa tài khoản. Không tự nhập kết quả cũ không rõ chủ sở hữu.
- `apps/web/public/index.html`, `dist/index.html` — Version 3.5.5.
- `apps/api/app/modules/graphrag/profile_context.py` — Đọc hồ sơ bằng user_id từ JWT; tính tổng THPT từ ba môn, chọn tổ hợp có tổng cao nhất khi câu hỏi không chỉ định; câu hỏi có điểm/khối/ngân sách được ưu tiên. Dùng RIASEC đã lưu thay suy luận từ khóa; thêm ngữ cảnh MBTI/GPA/chứng chỉ/quê quán/thể lực cho báo cáo.
- `apps/api/app/modules/graphrag/router.py` — Cả hai endpoint recommend yêu cầu đăng nhập, đọc hồ sơ; giữ lỗi 422/503; bỏ fallback chứa số liệu giả; sửa lỗi SSE đọc portfolio.summary không tồn tại.
- `apps/api/app/modules/graphrag/models/recommendation.py`, `llm_service.py` — Thêm ngữ cảnh hồ sơ không chứa tên/email; xử lý ngân sách chưa cung cấp.
- `apps/api/tests/test_profile_recommendations.py`, `tests/quiz-auth.test.cjs` — Kiểm thử tích hợp và đồng bộ theo tài khoản.

**Kết quả**:
- ✅ 10 kiểm thử backend đạt (JWT bắt buộc, chọn đúng user_id, điểm 0, dữ liệu thiếu, không lấy GPA thay THPT, RIASEC bắt buộc, ngữ cảnh báo cáo, SSE, lỗi Neo4j không fallback giả).
- ✅ Node syntax và kiểm thử frontend đạt (hàng đợi đúng tài khoản, gửi token, giữ dữ liệu khi lưu thất bại); sync public/dist.
- ✅ Máy chủ restart; health xác nhận PostgreSQL/Neo4j hoạt động và API tư vấn không đăng nhập trả 401. Ollama local offline không chứng minh provider cloud hoạt động; không gọi mô hình trả phí trong kiểm thử.

**Lưu ý**:
- Luồng xét tuyển này hiện chỉ dùng THPT /30; không quy đổi GPA/ĐGNL/IELTS thành điểm THPT. Thiếu ba môn hợp lệ hoặc RIASEC trả hướng dẫn bổ sung, không tự gán 25 điểm/RIA.
- Chưa cộng điểm ưu tiên vào điểm THPT của luồng này; ghi rõ trong ngữ cảnh. Thể lực bỏ trống chưa được xác minh. Quê quán không tự coi là địa điểm muốn học.
- Cognitive lưu vào competency; Big Five lưu riêng, chưa dùng để thay RIASEC trong bộ lọc. Kết quả trắc nghiệm cũ chỉ nằm ở localStorage không tự gắn cho tài khoản.
- Bảng sửa hồ sơ cũ `#ho-so` vẫn có nút lưu local; luồng nhập mới `#thiet-lap-ho-so` lưu API. Cần đồng bộ trang chỉnh sửa cũ trong task riêng nếu tiếp tục dùng nó.

---

## [2026-11-13] Codex — Luồng nhập hồ sơ sau đăng nhập

**Files đã thay đổi**:
- `apps/web/public/app.js`, `apps/web/dist/app.js` — Học sinh đăng nhập/đăng ký chuyển đến `#thiet-lap-ho-so`: cá nhân/quê quán → học bạ/điểm thi → tài chính/thể lực → trắc nghiệm. Admin tiếp tục vào quản trị.
- `apps/web/public/index.html`, `apps/web/dist/index.html` — Version 3.5.4.
- `tests/quiz-auth.test.cjs` — Cập nhật điều hướng qua hồ sơ trước khi tiếp tục bài đã chọn.

**Kết quả**:
- ✅ Mỗi lần đăng nhập tải hồ sơ từ API tài khoản hiện tại, điền sẵn dữ liệu đã lưu; không dùng thông tin mẫu của trình duyệt trong form mới.
- ✅ Cá nhân yêu cầu họ/tên, trường, quê quán; học bạ yêu cầu GPA 0–10. Điểm thi/chứng chỉ chưa có để trống; giữ điểm 0 đúng.
- ✅ Lưu từng bước qua PUT profile/background/academic/health; lỗi lưu giữ tại form, có thông báo và cho thử lại. Có quay lại; tài chính/thể lực có nút bỏ qua không gửi dữ liệu bước này.
- ✅ Hoàn tất tới danh sách trắc nghiệm hoặc bài đã chọn trước đăng nhập.
- ✅ Node syntax và kiểm thử logic đạt. Chrome CDP với API giả lập xác minh chuyển ba bước, dữ liệu lưu, điểm 0, ô trống và bỏ qua tới trắc nghiệm; không sửa hồ sơ thật khi kiểm thử.

---

## [2026-11-13] Codex — Thiết kế lại thanh điều hướng không dồn chữ

**Files đã thay đổi**:
- `apps/web/public/index.html`, `styles.css`, `app.js` và bản sync trong `dist/` — Header rộng tối đa 1480px, logo và nhãn giữ một dòng, chiều cao 76px, khoảng cách đồng đều; nút hồ sơ gọn, admin/đăng xuất dùng icon kèm tên truy cập khi thiếu chỗ; menu thu gọn dưới 1300px. Bump app 3.5.3, CSS 2.3.2.
- `docs/TODO.md` — Ghi nhận hoàn thành.

**Kết quả**:
- ✅ Kiểm thử trực tiếp Chrome headless qua CDP: 320, 390, 768, 1024, 1200, 1280, 1307, 1440, 1920px; cả khách, học sinh và admin không tràn ngang hoặc dồn nhãn.
- ✅ Menu di động mở được; đã xem ảnh chụp header admin 1307px.
- ✅ Node syntax check, sync source/dist.

---

## [2026-11-13] Codex — Đăng nhập bắt buộc khi làm trắc nghiệm và tài khoản admin riêng

**Agent**: Codex  
**Files đã thay đổi**:
- `apps/web/public/app.js`, `apps/web/dist/app.js` — Xác thực phiên qua API trước khi mở bài; nhớ bài đã chọn và tiếp tục sau đăng nhập/đăng ký; lựa chọn đăng nhập admin chỉ bằng mật khẩu; bỏ nút điền sẵn tài khoản mẫu.
- `apps/web/public/index.html`, `apps/web/dist/index.html` — Cache version 3.5.2.
- `apps/api/app/modules/auth/schemas.py`, `router.py` — Chuẩn hóa bỏ khoảng trắng mật khẩu trước validation; endpoint `/api/v1/auth/admin-login` chỉ xác thực tài khoản admin chuyên dụng.
- `tests/quiz-auth.test.cjs` — Kiểm tra khách, phiên hết hạn, phiên hợp lệ và điều hướng sau đăng nhập.

**Kết quả**:
- ✅ Tạo thêm `owner@foryourfuture.edu.vn` trong PostgreSQL, role admin; mật khẩu chỉ lưu dạng hash, không ghi vào source/docs.
- ✅ Node syntax check, Python compile, kiểm thử luồng quiz bằng Node VM đều đạt.
- ✅ API thực tế: admin đăng nhập với/không khoảng trắng, sai mật khẩu trả 401, `/auth/me`, API trắc nghiệm yêu cầu xác thực, đăng nhập học sinh hiện có và DB health đều đạt.
- ✅ Khởi động lại FastAPI cổng 8000 và sync public/dist.

**Lưu ý cho AI tiếp theo**:
- Tài khoản admin chuyên dụng được tạo trực tiếp trong DB; không hardcode mật khẩu hoặc tự động tạo lại khi startup.
- Chưa kiểm thử giao diện bằng trình duyệt: môi trường Python/Node chưa có Playwright/Puppeteer. Đã kiểm thử logic frontend bằng Node VM và backend bằng HTTP thực tế.

---

## [2026-11-13] Antigravity — Thiết lập hệ thống tài liệu chia sẻ AI

**Agent**: Antigravity  
**Thời gian**: 2026-11-13 16:36 (GMT+7)  
**Files đã thay đổi**:
- `AGENTS.md` — Tạo mới - quy tắc bắt buộc cho AI agents
- `docs/PROJECT_CONTEXT.md` — Tạo mới - ngữ cảnh đầy đủ dự án
- `docs/WORK_HISTORY.md` — Tạo mới - lịch sử công việc
- `docs/TODO.md` — Tạo mới - danh sách việc cần làm
- `.agent-lock/` — Tạo thư mục cơ chế lock
- `scripts/log_work.py` — Tạo mới - script tự động log
- `scripts/lock.py` — Tạo mới - script quản lý lock

**Kết quả**:
- ✅ 4 file tài liệu chia sẻ hoạt động
- ✅ Cơ chế lock tránh edit đồng thời
- ✅ Script log_work.py để AI tự động cập nhật
- ✅ Script lock.py để quản lý file lock

**Lưu ý cho AI tiếp theo**:
- Codex đọc AGENTS.md trước khi làm việc. Server cần bypass sandbox.

---

## [2026-11-13] Antigravity — Thiết lập hệ thống tài liệu chia sẻ AI

**Agent**: Antigravity AI  
**Thời gian**: 2026-11-13 16:35 (GMT+7)  
**Files đã tạo/thay đổi**:
- `AGENTS.md` ← Tạo mới — Quy tắc bắt buộc cho mọi AI agent
- `docs/PROJECT_CONTEXT.md` ← Tạo mới — Toàn bộ ngữ cảnh dự án
- `docs/WORK_HISTORY.md` ← Tạo mới (file này)
- `docs/TODO.md` ← Tạo mới — Danh sách việc cần làm
- `.agent-lock/` ← Tạo thư mục cơ chế lock

**Kết quả**:
- ✅ Hệ thống tài liệu chia sẻ 4 file hoạt động
- ✅ Cơ chế lock file để tránh edit đồng thời
- ✅ Phân tích và tổng hợp đầy đủ kiến trúc hiện tại vào PROJECT_CONTEXT.md
- ✅ Tổng hợp lịch sử công việc từ conversation transcript vào WORK_HISTORY.md

**Lưu ý cho AI tiếp theo**:
- Server cần bypass sandbox để khởi động: `BypassSandbox: true`
- app.js dùng LF encoding (không phải CRLF), không dùng `edit_file` cho multi-line targets
- PostgreSQL Aiven cần internet — nếu sandbox, dùng SQLite fallback

---

## [2026-11-13] Antigravity — Nâng cấp bảng ngành chi tiết trường

**Agent**: Antigravity AI  
**Thời gian**: 2026-11-13 09:15 (GMT+7)  
**Files đã thay đổi**:
- `apps/web/public/app.js` (line 3613–3703) — Nâng cấp `renderSchoolProgramRows`
- `apps/web/public/index.html` — Bump version → `v=3.5.1`
- `apps/web/dist/app.js` — Sync
- `apps/web/dist/index.html` — Sync

**Kết quả**:
- ✅ **Live badge** 🟢 `animate-pulse` trên trang danh sách 126 trường ("Dữ liệu trực tiếp từ cơ sở dữ liệu")
- ✅ **Grouped program rows**: mỗi ngành = 1 hàng (trước: mỗi phương thức = 1 hàng)
- ✅ **Thêm cột Học bạ** (thang /30, màu amber-700)
- ✅ **Thêm cột Học phí** (triệu/năm, màu cyan)
- ✅ Tổ hợp hiển thị inline bên dưới tên ngành
- ✅ `tuition_annual` được map từ API response vào program object

**Lưu ý cho AI tiếp theo**:
- Bảng ngành hiện có 8 cột: #, Mã XT, Tên ngành & Tổ hợp, THPT, ĐGTD, Kết hợp, Học bạ, Học phí

---

## [2026-11-12] Antigravity — Seed dữ liệu 126 trường lên PostgreSQL

**Agent**: Antigravity AI  
**Thời gian**: 2026-11-12 21:00 (GMT+7)  
**Files đã thay đổi**:
- `apps/web/public/app.js` — Thêm `renderSchoolDetailPage` async (API-first + fallback)
- `apps/web/public/data/school_details.json` — Tạo mới (3.3MB, 7868 rows)
- `apps/api/foryourfuture.db` — SQLite seed
- Aiven PostgreSQL — Seed production

**Kết quả**:
- ✅ **126 universities** seeded vào PostgreSQL Aiven
- ✅ **3,482 unique programs** seeded
- ✅ **14,547 admission_criteria rows** seeded
- ✅ API endpoint `GET /api/v1/universities/{uni_id}` trả dữ liệu đầy đủ
- ✅ Route `#truong-dai-hoc/uni-XXX` → `renderSchoolDetailPage(container, 'uni-XXX')`
- ✅ Trang chi tiết trường: Header, Stats cards, Score range, Bảng ngành

**Script đã dùng**:
- `brain/scratch/extract_school_data.py` — Extract từ Excel → JSON
- `brain/scratch/seed_to_postgres.py` — Seed JSON → PostgreSQL

**Data quality fixes**:
- THPT > 30 → NULL (do formula cell Excel trả về giá trị học phí)
- Học bạ > 100 → NULL
- Kết hợp > 1200 → NULL

---

## [2026-11-12] Antigravity — Thêm logo chính thức vào website

**Agent**: Antigravity AI  
**Thời gian**: 2026-11-12 13:15 (GMT+7)  
**Files đã thay đổi**:
- `apps/web/public/logo.jpg` — Thêm logo mới (tay nắm + orbit xanh)
- `apps/web/public/index.html` — Thay favicon, header logo, footer logo

**Kết quả**:
- ✅ Logo `/logo.jpg` hiển thị trong header (40×40px), footer (32×32px), favicon
- ✅ Thay thế beacon SVG cũ

---

## [2026-11-12] Antigravity — Trang detail trường với MBTI & RIASEC animated SVG

**Agent**: Antigravity AI  
**Thời gian**: 2026-11-12 (GMT+7)  
**Mô tả**: Thêm SVG animated cho 16 MBTI types và RIASEC groups  

**Kết quả**:
- ✅ 16 × `MBTI_XXXX_animated.svg` phục vụ từ `/personality/`
- ✅ RIASEC 3-avatar triplet: chữ đứng đầu to nhất, 2 chữ còn lại nhỏ hơn
- ✅ Card kết quả personality: icon to, text mô tả rộng hơn, không bị gộp

---

## [2026-11-11] Antigravity — Khởi tạo kiến trúc ban đầu

**Agent**: Antigravity AI  
**Thời gian**: 2026-11-11 (GMT+7)  
**Mô tả**: Xây dựng SPA ban đầu với các tính năng cốt lõi

**Kết quả**:
- ✅ FastAPI backend với 10+ modules
- ✅ Frontend SPA app.js (~4000 dòng lúc ban đầu)
- ✅ Authentication JWT
- ✅ Quiz RIASEC 60 câu + MBTI
- ✅ Hồ sơ học sinh 4 tab
- ✅ Tư vấn AI với GraphRAG (Neo4j + LLM grounding)
- ✅ Danh sách 126 trường đại học
- ✅ Design system: Navy/Azure/Cyan tokens, Plus Jakarta Sans + Be Vietnam Pro
