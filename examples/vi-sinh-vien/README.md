# Ví Sinh Viên — Quản lý thu chi

Ứng dụng web thực hành để quản lý khoản thu, chi và ngân sách theo tháng. Trợ lý cục bộ có thể tách mô tả ngắn như “ăn trưa 35k hôm nay” thành các trường giao dịch để người dùng xác nhận trước khi lưu. Đây là dự án độc lập trong fork OpenClaw, không phải chức năng tích hợp sẵn của OpenClaw và không gọi Gateway hoặc mô hình AI.

## Cấu trúc thư mục

- index.html — form, bảng, tổng quan và vùng thông báo
- styles.css — giao diện responsive
- index.js — máy chủ tĩnh Node.js trên localhost
- package.json — lệnh start, check và test
- start.bat — kiểm tra và chạy trên Windows
- src/main.js — khởi tạo ứng dụng, sự kiện UI và điều phối
- src/input.js — xác thực form và dữ liệu JSON nhập vào
- src/output.js — định dạng tiền/ngày, dựng hàng giao dịch, xuất tệp
- src/storage.js — lưu/đọc/xóa localStorage
- src/finance.js — tổng thu chi, số dư, nhóm danh mục
- src/config.js — danh mục và cấu hình
- src/assistant.js — gợi ý danh mục, phát hiện mẫu chi tiêu lặp và phân tích ngày/tháng/năm
- tests/input.test.js — kiểm thử dữ liệu đầu vào bằng node:test
- tests/assistant.test.js — kiểm thử gợi ý danh mục và phân tích theo ngày/tháng/năm bằng node:test

## Chạy trên Windows / VS Code

Mở đúng thư mục examples/vi-sinh-vien trong VS Code rồi chạy trong Terminal:

    node --version
    npm.cmd run check
    npm.cmd test
    npm.cmd start

Mở http://127.0.0.1:5500. Dừng máy chủ bằng Ctrl+C. Hoặc bấm đúp start.bat. Không cần npm install vì app không dùng thư viện ngoài.

## Chức năng

- Bảng tổng quan số dư, tổng thu, tổng chi và tỷ lệ tiết kiệm theo tháng.
- Thêm, sửa, xóa, tìm kiếm giao dịch.
- Nhập nhanh từ mô tả tự nhiên: thử “ăn trưa 35k hôm nay” hoặc “nhận lương làm thêm 2 triệu hôm qua”; trợ lý tách loại, tiền, ngày và danh mục để người dùng kiểm tra trước khi lưu.
- Gợi ý tự động danh mục theo tên/nội dung giao dịch.
- Trợ lý phân tích theo ngày, tháng hoặc năm; so sánh kỳ liền trước, nhận diện danh mục chiếm tỷ trọng lớn và phát hiện khoản chi lặp qua nhiều tháng.
- Gợi ý mức chi theo ngân sách, cảnh báo vượt ngân sách và mẹo tiết kiệm dựa trên dữ liệu đã ghi.
- Phân loại khoản thu/chi và thống kê chi tiêu theo danh mục.
- Đặt giới hạn ngân sách theo tháng và xem phần đã dùng/còn lại.
- Xuất CSV, sao lưu và khôi phục JSON.
- Lưu cục bộ bằng localStorage; không có tài khoản, backend, đồng bộ đám mây hay kết nối ngân hàng.

## Trợ lý chi tiêu thông minh

Trợ lý dùng quy tắc từ khóa, phân tích câu nhập nhanh và phép tính thống kê ngay trong trình duyệt, không gọi API AI và không gửi dữ liệu giao dịch ra ngoài. Chọn Ngày/Tháng/Năm cùng ngày mốc để xem tổng thu, tổng chi, xu hướng so với kỳ liền trước, danh mục chiếm tỷ trọng lớn, ngân sách và gợi ý hành động. Khi nhập tên giao dịch, ứng dụng đề xuất danh mục phù hợp; người dùng vẫn có thể sửa. Mẫu chi tiêu trùng tên ở nhiều tháng được đánh dấu là khoản có thể định kỳ, không tự tạo giao dịch thay người dùng.

## Các thành phần đã tận dụng

- HTML cho form nhập liệu, bảng giao dịch, bộ lọc và tổng quan.
- CSS cho bố cục responsive, thẻ thống kê, thanh tiến độ và giao diện di động.
- JavaScript ES modules để tách main, input, output, storage, finance, config và assistant.
- DOM và event listeners để đọc đầu vào, kiểm tra dữ liệu, cập nhật giao diện.
- Intl.NumberFormat, localStorage, Blob, FileReader và URL.createObjectURL cho hiển thị tiền, lưu dữ liệu và nhập/xuất tệp.
- Node.js built-in modules (http, fs, path, url) làm máy chủ web đơn giản; không cài dependency.
- node:test để chạy kiểm thử cơ bản cho dữ liệu đầu vào và file sao lưu.
- GitHub fork để lưu trữ source, theo dõi commit và ghi tài liệu sử dụng trong README.

Ứng dụng hiện có trợ lý phân tích theo quy tắc chạy cục bộ, không phải mô hình AI học máy/tạo sinh và OpenClaw chưa được tích hợp làm backend. Để tích hợp mô hình AI thực sự sau này cần xây dựng lớp dịch vụ/connector riêng, giữ API key ở phía máy chủ và thiết kế rõ quyền truy cập dữ liệu tài chính.
