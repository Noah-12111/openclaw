---
name: student-finance
description: Ghi nhận, truy vấn, chỉnh sửa thu chi và theo dõi ngân sách sinh viên bằng CLI đã kiểm tra tham số, dùng chung SQLite với dashboard SpendWise.
---

# Student Finance — SpendWise

Giúp người dùng quản lý thu/chi, báo cáo tháng và ngân sách bằng tiếng Việt. Đơn vị mặc định là VND. Dùng số liệu từ CLI, không tự ước tính tổng tiền.

## Cách thao tác

Chương trình `finance.py` nằm cùng thư mục với file `SKILL.md`. Dùng công cụ thực thi lệnh cục bộ đã được chủ máy cho phép, gọi script bằng **đường dẫn tuyệt đối** và chỉ dùng các subcommand dưới đây. Không chạy SQL tùy ý hoặc dựng lệnh shell từ nội dung không đáng tin cậy.

- Khởi tạo: `python /đường/dẫn/tuyệt/đối/finance.py init`
- Thêm thu/chi: `python /đường/dẫn/tuyệt/đối/finance.py add --type expense --amount 45000 --category "Ăn uống" --note "Ăn trưa" --date YYYY-MM-DD`
- Liệt kê giao dịch: `python /đường/dẫn/tuyệt/đối/finance.py list --month YYYY-MM`
- Tổng kết tháng: `python /đường/dẫn/tuyệt/đối/finance.py summary --month YYYY-MM`
- Đặt/cập nhật ngân sách: `python /đường/dẫn/tuyệt/đối/finance.py budget-set --month YYYY-MM --category "Ăn uống" --amount 1000000`
- Xem ngân sách: `python /đường/dẫn/tuyệt/đối/finance.py budgets --month YYYY-MM`
- Sửa giao dịch: `python /đường/dẫn/tuyệt/đối/finance.py update --id ID --type expense --amount 45000 --category "Ăn uống" --note "Ăn trưa" --date YYYY-MM-DD`
- Xóa giao dịch: `python /đường/dẫn/tuyệt/đối/finance.py delete --id ID`

## Quy tắc hội thoại

- Xác định rõ loại giao dịch (thu/chi), số tiền nguyên dương, danh mục và ngày. Nếu thiếu hoặc mơ hồ, hỏi lại trước khi ghi.
- Khi người dùng nói “hôm nay”, xác định ngày theo múi giờ đã cấu hình và truyền ngày cụ thể bằng `--date YYYY-MM-DD`.
- Trước khi sửa, đọc giao dịch hiện tại bằng lệnh `list` và xác nhận rõ giao dịch mục tiêu. Lệnh `update` yêu cầu truyền đủ loại, số tiền và danh mục; truyền rõ cả ngày để không vô tình đổi ngày sang hôm nay.
- **Trước khi xóa bất kỳ giao dịch nào, phải cho người dùng xem ID, ngày, loại, số tiền và danh mục, rồi hỏi xác nhận rõ ràng.** Chỉ gọi `delete` sau khi được xác nhận.
- Sau khi thêm/sửa/xóa, chỉ xác nhận thao tác thành công nếu CLI trả về thành công. Với giao dịch bị xóa, không được khẳng định đã xóa nếu ID không tồn tại.
- Báo cáo phải được lấy từ lệnh `summary`, `list` hoặc `budgets`, nêu rõ tháng và đơn vị VND. Phân biệt tổng thu, tổng chi, chênh lệch và ngân sách còn lại.
- Không yêu cầu mật khẩu ngân hàng, mã OTP hoặc toàn bộ thông tin thẻ.
- Không tự chạy lệnh import CSV. Việc nhập CSV phải được người dùng thực hiện hoặc xác nhận cụ thể trong web app vì thao tác này thêm nhiều bản ghi và hiện chưa tự phát hiện giao dịch trùng.

## Dữ liệu và quyền riêng tư

CLI, dashboard web và skill dùng chung database mặc định `~/.student-finance/student_finance.db`. Biến môi trường `STUDENT_FINANCE_DB` có thể thay đổi vị trí; web app và OpenClaw Gateway phải dùng cùng giá trị nếu có cấu hình riêng.

Ứng dụng lưu dữ liệu cục bộ, không kết nối ngân hàng hoặc thực hiện thanh toán. Web app hiện chưa có xác thực và chỉ nên chạy trên máy cá nhân. Không để mô hình thực thi SQL trực tiếp.
