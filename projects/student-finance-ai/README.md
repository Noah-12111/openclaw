# SpendWise — Student Finance AI

Ứng dụng quản lý thu chi cá nhân dành cho sinh viên. **Dashboard web, CLI Python và skill OpenClaw dùng chung một file SQLite**, nên giao dịch ghi từ nơi nào cũng được phản ánh trong cùng báo cáo.

## Tính năng

- **Dashboard tiếng Việt:** tổng thu, tổng chi, chênh lệch thu–chi, số lượng giao dịch và biểu đồ thanh chi tiêu theo danh mục.
- **Quản lý giao dịch đầy đủ:** thêm, sửa, xóa có hộp thoại xác nhận; kiểm tra số tiền, danh mục, ghi chú và ngày.
- **Tìm kiếm và lọc:** tìm theo ghi chú/danh mục, lọc theo loại thu/chi và danh mục, chọn tháng báo cáo.
- **Ngân sách theo tháng:** đặt hoặc cập nhật hạn mức theo danh mục, xem số đã dùng/còn lại, xóa ngân sách mà không ảnh hưởng đến giao dịch.
- **CSV:** xuất giao dịch trong tháng và nhập giao dịch từ CSV. File nhập được xác thực toàn bộ trước khi ghi; nếu một dòng không hợp lệ thì không có dòng nào được thêm. Import là thao tác thêm mới và không tự dò giao dịch trùng.
- **CLI cho automation:** thêm, liệt kê, tổng kết, đặt ngân sách, sửa và xóa giao dịch bằng Python.
- **Tính toán xác định:** tổng tiền được tính bằng Python/SQLite, không để mô hình AI tự ước tính.
- **Chạy cục bộ:** chỉ dùng thư viện chuẩn Python, không cần tài khoản dịch vụ bên ngoài hoặc kết nối ngân hàng.

## Yêu cầu

Python 3.10 trở lên.

## Chạy trên Windows

Từ thư mục `projects/student-finance-ai`:

```powershell
py -3 finance.py init
py -3 web_app.py
```

Mở http://127.0.0.1:8765. Giữ cửa sổ Terminal chạy máy chủ mở trong khi sử dụng. Dừng máy chủ bằng `Ctrl+C`.

Trên Linux/macOS có thể dùng `python3` thay cho `py -3`.

## Dùng CLI

```powershell
# Thêm khoản chi
py -3 finance.py add --type expense --amount 45000 --category "Ăn uống" --note "Ăn trưa"

# Xem giao dịch và báo cáo
py -3 finance.py list --month 2026-10
py -3 finance.py summary --month 2026-10

# Đặt hoặc cập nhật ngân sách
py -3 finance.py budget-set --month 2026-10 --category "Ăn uống" --amount 1000000
py -3 finance.py budgets --month 2026-10

# Sửa một giao dịch theo ID
py -3 finance.py update --id 1 --type expense --amount 50000 --category "Ăn uống" --note "Cập nhật" --date 2026-10-28

# Xóa giao dịch theo ID (CLI không có hộp thoại xác nhận)
py -3 finance.py delete --id 1
```

Khi sửa, cung cấp đủ loại, số tiền và danh mục. Nếu không truyền `--date`, chương trình dùng ngày hiện tại; với lệnh `update`, hãy truyền rõ ngày để tránh thay đổi ngày ngoài ý muốn.

## Dữ liệu dùng chung

Mặc định database được lưu tại:

```text
~/.student-finance/student_finance.db
```

Trên Windows, thư mục `~` tương ứng thư mục hồ sơ người dùng hiện hành. Vị trí ổn định cho phép CLI, web app và skill sử dụng cùng cơ sở dữ liệu dù được chạy từ các thư mục khác nhau.

Có thể đặt biến môi trường `STUDENT_FINANCE_DB` để đổi vị trí. Khi đó, hãy đặt cùng giá trị cho tiến trình web app và OpenClaw Gateway. Không xóa file database nếu chưa sao lưu.

## CSV

Định dạng CSV yêu cầu các cột:

```csv
transaction_date,kind,amount_vnd,category,note
2026-10-28,expense,45000,food,Lunch
2026-10-29,income,1500000,allowance,Monthly allowance
```

Ngày dùng định dạng `YYYY-MM-DD`; loại là `income` hoặc `expense`; số tiền là số nguyên dương theo VND. Web app giới hạn file nhập ở 2 MB và 5.000 giao dịch. Nhập CSV sẽ **thêm** dòng mới, không tự động ghi đè hoặc loại giao dịch trùng; hãy kiểm tra file trước khi nhập.

## Cài skill OpenClaw

1. Sao chép **toàn bộ thư mục** `student-finance-ai` vào thư mục skills của workspace, ví dụ `<workspace>/skills/student-finance/`.
2. Đảm bảo thư mục skill có `SKILL.md` và `finance.py`, sau đó nạp lại Gateway theo quy trình của bản OpenClaw đang dùng.
3. Cho phép skill gọi công cụ thực thi lệnh cục bộ theo cấu hình giới hạn an toàn. Trợ lý cần dùng đường dẫn tuyệt đối tới `finance.py`, không giả định thư mục làm việc hiện tại.
4. Khởi tạo database một lần bằng `python finance.py init`. Nếu web app và Gateway chạy với cùng tài khoản người dùng và không ghi đè `STUDENT_FINANCE_DB`, chúng sẽ dùng chung file SQLite.
5. Với xóa giao dịch hoặc thao tác phá hủy dữ liệu, trợ lý phải xác nhận ý định rõ ràng trước khi gọi lệnh.

Skill này là lớp hướng dẫn cho trợ lý, **không tự đăng ký plugin/tool riêng**. Khả năng dùng lệnh phụ thuộc công cụ thực thi đã được bật trong OpenClaw. Không cho mô hình chạy SQL tùy ý.

## Kiểm thử

```powershell
py -3 -m unittest discover -s tests -v
```

Bộ kiểm thử bao gồm phép tính thu chi, ranh giới tháng, lọc/tìm kiếm, sửa/xóa giao dịch, ngân sách, CSV import theo cơ chế all-or-nothing và HTTP API. GitHub Actions chạy cùng bộ test khi thay đổi thư mục dự án.

## An toàn và giới hạn

- Máy chủ chỉ bind vào loopback `127.0.0.1` theo mặc định và từ chối địa chỉ bind ngoài loopback.
- **Chưa có đăng nhập.** Không mở cổng web app ra Internet hoặc mạng LAN; chỉ dùng trên máy cá nhân.
- Dữ liệu lưu cục bộ; không kết nối ngân hàng, không chuyển tiền, không đồng bộ từ xa.
- Xuất file CSV có thể đưa dữ liệu thu chi ra khỏi máy; hãy lưu và chia sẻ file cẩn thận.
- Không nhập mật khẩu ngân hàng, OTP hay toàn bộ thông tin thẻ.
- Dữ liệu nhập từ CSV chỉ được xác thực định dạng; hãy chỉ nhập file từ nguồn bạn tin cậy.
- Đây là công cụ lập ngân sách cá nhân, không phải tư vấn tài chính, thuế hay đầu tư.
