# Student Finance AI — SpendWise

Ứng dụng quản lý thu chi dành cho sinh viên. **Web app, CLI Python và skill OpenClaw dùng chung một cơ sở dữ liệu SQLite**, nên giao dịch được ghi ở giao diện nào cũng xuất hiện ở giao diện còn lại.

## Tính năng hiện có

- Ghi khoản thu/chi với số tiền VND, danh mục, ngày và ghi chú.
- Dashboard web tiếng Việt: tổng thu, tổng chi, số dư, danh sách giao dịch và phân tích chi theo danh mục.
- Đặt ngân sách từng danh mục theo tháng và theo dõi mức đã dùng/còn lại.
- CLI Python cho các thao tác tương tự; OpenClaw skill hướng dẫn trợ lý gọi CLI bằng công cụ thực thi lệnh được cấu hình.
- Tất cả phép tính được thực hiện trong Python/SQLite, không để mô hình tự đoán tổng tiền.
- Chỉ dùng thư viện chuẩn Python, không cần cài package bên thứ ba.

## Yêu cầu

Python 3.10 trở lên.

## Chạy web app

Từ thư mục `projects/student-finance-ai`:

```bash
python finance.py init
python web_app.py
```

Mở http://127.0.0.1:8765 trên cùng máy. Máy chủ chỉ bind vào địa chỉ loopback để mặc định không mở dashboard ra mạng LAN/Internet.

## Dùng CLI

```bash
python finance.py add --type expense --amount 45000 --category food --note "Ăn trưa"
python finance.py add --type income --amount 1500000 --category allowance --note "Tiền sinh hoạt"
python finance.py list --month 2026-10
python finance.py summary --month 2026-10
python finance.py budget-set --month 2026-10 --category food --amount 1000000
python finance.py budgets --month 2026-10
```

## Cơ sở dữ liệu dùng chung

Mặc định database được lưu trong thư mục home của người dùng tại:

```text
~/.student-finance/student_finance.db
```

Vị trí ổn định này giúp CLI, web app và bản skill được cài ở thư mục khác vẫn nhìn thấy cùng dữ liệu. Có thể đặt biến môi trường `STUDENT_FINANCE_DB` để đổi đường dẫn; nếu đổi, hãy đặt cùng giá trị cho tiến trình web app và tiến trình OpenClaw Gateway.

## Cài skill OpenClaw

1. Sao chép **toàn bộ thư mục** `student-finance-ai` vào thư mục skills của workspace OpenClaw, ví dụ `<workspace>/skills/student-finance/`. Thư mục cài đặt cần chứa cả `SKILL.md` và `finance.py`.
2. Đảm bảo OpenClaw đã nạp skill theo cấu hình workspace. Nếu vừa cài mới, khởi động lại/làm mới Gateway theo quy trình của bản OpenClaw bạn đang dùng.
3. Cho phép skill dùng công cụ thực thi lệnh cục bộ theo cấu hình an toàn của bạn. Khi cần gọi CLI, trợ lý phải dùng **đường dẫn tuyệt đối** tới `finance.py` trong thư mục skill; không giả định thư mục làm việc hiện tại.
4. Chạy `python finance.py init` một lần (hoặc gọi lệnh `init` với đường dẫn tuyệt đối). Web app và skill sẽ dùng chung database mặc định trong thư mục home.

Skill là lớp hướng dẫn cho trợ lý, không phải plugin tự đăng ký API tool riêng. Các thao tác ghi phải đi qua CLI đã kiểm tra tham số; không cho mô hình chạy SQL tùy ý. Khả năng gọi lệnh phụ thuộc việc công cụ thực thi lệnh đã được bật và giới hạn trong OpenClaw hay chưa.

## Chạy kiểm thử

```bash
python -m unittest discover -s tests -v
```

Bộ kiểm thử bao gồm business logic, kiểm tra ngày/tháng, ngân sách và HTTP API dùng cùng SQLite.

## Dữ liệu và an toàn

- Lưu cục bộ; không kết nối ngân hàng, không chuyển tiền, không tự gửi dữ liệu ra dịch vụ ngoài.
- Máy chủ web hiện chưa có đăng nhập, vì vậy chỉ chạy trên máy cá nhân và không expose ra mạng.
- Không nhập mật khẩu ngân hàng, OTP hoặc toàn bộ thông tin thẻ.
- Sao lưu file database một cách an toàn.
- Hiện chưa có chức năng sửa/xóa giao dịch, nhập sao kê ngân hàng hoặc đồng bộ nhiều thiết bị.
- Đây là công cụ lập ngân sách cá nhân, không phải tư vấn tài chính, thuế hay đầu tư.
