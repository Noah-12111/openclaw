# Ví Sinh Viên — Quản lý thu chi

Ứng dụng web thực hành để quản lý khoản thu, chi và ngân sách theo tháng. Đây là dự án độc lập trong fork OpenClaw, không phải chức năng tích hợp sẵn của OpenClaw và không gọi Gateway hoặc mô hình AI.

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
- tests/input.test.js — kiểm thử validation bằng node:test

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
- Phân loại khoản thu/chi và thống kê chi tiêu theo danh mục.
- Đặt giới hạn ngân sách theo tháng và xem phần đã dùng/còn lại.
- Xuất CSV, sao lưu và khôi phục JSON.
- Lưu cục bộ bằng localStorage; không có tài khoản, backend, đồng bộ đám mây hay kết nối ngân hàng.

## Các thành phần đã tận dụng

- HTML cho form nhập liệu, bảng giao dịch, bộ lọc và tổng quan.
- CSS cho bố cục responsive, thẻ thống kê, thanh tiến độ và giao diện di động.
- JavaScript ES modules để tách main, input, output, storage, finance và config.
- DOM và event listeners để đọc đầu vào, kiểm tra dữ liệu, cập nhật giao diện.
- Intl.NumberFormat, localStorage, Blob, FileReader và URL.createObjectURL cho hiển thị tiền, lưu dữ liệu và nhập/xuất tệp.
- Node.js built-in modules (http, fs, path, url) làm máy chủ web đơn giản; không cài dependency.
- node:test để chạy kiểm thử cơ bản cho dữ liệu đầu vào và file sao lưu.
- GitHub fork để lưu trữ source, theo dõi commit và ghi tài liệu sử dụng trong README.

OpenClaw chưa được tích hợp làm backend hoặc AI cho ứng dụng thu–chi này. Để tích hợp sau này cần xây dựng một lớp dịch vụ/connector riêng và thiết kế rõ quyền truy cập dữ liệu tài chính.
