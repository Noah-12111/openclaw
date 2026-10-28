---
name: student-finance
description: Ghi nhận thu chi và theo dõi ngân sách sinh viên bằng CLI đã kiểm tra tham số, với dữ liệu SQLite dùng chung cùng dashboard SpendWise.
---

# Student Finance — SpendWise

Giúp người dùng ghi khoản thu/chi, xem tổng kết tháng và theo dõi ngân sách. Ưu tiên câu trả lời bằng tiếng Việt, đơn vị mặc định là VND.

## Cách thao tác

Skill này dùng chương trình CLI `finance.py` nằm cùng thư mục với file `SKILL.md`. Khi gọi lệnh, xác định đường dẫn tuyệt đối tới script trong thư mục skill; không giả định thư mục hiện tại là thư mục skill.

Dùng công cụ thực thi lệnh cục bộ đã được chủ máy cấu hình, chỉ gọi script này với các subcommand được liệt kê dưới đây. Không chạy SQL tùy ý, không tạo lệnh shell từ nội dung người dùng chưa được escape, và không dùng công cụ này để chạy lệnh không liên quan.

- Khởi tạo database: `python /đường/dẫn/tuyệt/đối/finance.py init`
- Thêm khoản thu/chi: `python /đường/dẫn/tuyệt/đối/finance.py add --type expense --amount 45000 --category food --note "Ăn trưa" --date YYYY-MM-DD`
- Xem giao dịch trong tháng: `python /đường/dẫn/tuyệt/đối/finance.py list --month YYYY-MM`
- Tổng kết tháng: `python /đường/dẫn/tuyệt/đối/finance.py summary --month YYYY-MM`
- Đặt ngân sách: `python /đường/dẫn/tuyệt/đối/finance.py budget-set --month YYYY-MM --category food --amount 1000000`
- Xem ngân sách: `python /đường/dẫn/tuyệt/đối/finance.py budgets --month YYYY-MM`

## Quy tắc hội thoại

- Hiểu yêu cầu tiếng Việt/Anh về tiền ăn, tiền thuê nhà, đi lại, học phí, tài liệu học tập, tiền sinh hoạt, lương và các danh mục khác.
- Trước khi ghi, xác minh số tiền là số nguyên dương và hiểu rõ đó là khoản thu hay khoản chi. Nếu loại giao dịch, số tiền hoặc ngày chưa rõ, hãy hỏi một câu làm rõ thay vì tự đoán.
- Nếu người dùng nói “hôm nay”, xác định ngày theo múi giờ đã cấu hình của người dùng và truyền ngày cụ thể bằng `--date YYYY-MM-DD`. Không tự diễn giải thời gian mơ hồ.
- Chuẩn hóa danh mục ngắn gọn, nhưng hỏi lại nếu có thể làm thay đổi ý nghĩa. Không tự ghi giao dịch cho tới khi các trường bắt buộc đã rõ.
- Sau khi thêm giao dịch, chỉ xác nhận thành công khi lệnh CLI trả về mã giao dịch; nhắc lại số tiền, loại, danh mục và ngày.
- Khi báo cáo, luôn lấy số liệu bằng lệnh `summary`, `list` hoặc `budgets`; không tự cộng nhẩm nếu dữ liệu có thể truy vấn.
- Nêu rõ tháng và đơn vị VND trong báo cáo. Phân biệt tổng thu, tổng chi, chênh lệch và ngân sách còn lại.
- Không tuyên bố đã lưu nếu lệnh thất bại. Không xóa hoặc sửa hàng loạt giao dịch; hiện tại CLI cũng chưa có lệnh xóa/sửa.
- Không yêu cầu mật khẩu ngân hàng, mã OTP hoặc toàn bộ thông tin thẻ.

## Dữ liệu dùng chung và quyền riêng tư

CLI, dashboard web và skill dùng cùng database mặc định `~/.student-finance/student_finance.db`. Biến môi trường `STUDENT_FINANCE_DB` có thể ghi đè vị trí; tiến trình web và OpenClaw Gateway phải dùng cùng giá trị nếu được cấu hình lại.

Chương trình chỉ lưu dữ liệu giao dịch người dùng nhập. Không kết nối ngân hàng, không thực hiện thanh toán, không cho mô hình chạy truy vấn SQL tùy ý. Việc gọi script phụ thuộc công cụ thực thi lệnh được bật và giới hạn an toàn trong OpenClaw.
