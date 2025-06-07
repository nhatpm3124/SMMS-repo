# HƯỚNG DẪN TRIỂN KHAI DỰ ÁN CHO MÔI TRƯỜNG PRODUCTION

## Mục lục
1. [Tổng quan](#tổng-quan)
2. [Các bước chuẩn bị](#các-bước-chuẩn-bị)
3. [Dọn dẹp dự án](#dọn-dẹp-dự-án)
4. [Khởi động dự án](#khởi-động-dự-án)
5. [Cấu hình bổ sung](#cấu-hình-bổ-sung)
6. [Xử lý sự cố](#xử-lý-sự-cố)

## Tổng quan

Tài liệu này hướng dẫn cách triển khai dự án Hệ thống Quản lý Người dùng trong môi trường production. Để đảm bảo vận hành ổn định và an toàn, chúng ta cần loại bỏ các file test, debug, và cấu hình cho môi trường production.

## Các bước chuẩn bị

### Yêu cầu hệ thống

- **Node.js**: v18.x hoặc cao hơn
- **Python**: v3.9 hoặc cao hơn
- **PostgreSQL**: v14.x hoặc cao hơn
- **npm** hoặc **yarn** để quản lý phụ thuộc frontend
- **MacOS** hoặc **Linux** (Khuyến nghị)

### Cài đặt phụ thuộc

1. **Backend (Python)**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Frontend (Node.js)**:
   ```bash
   cd frontend
   npm install
   ```

3. **Cài đặt Serve để phục vụ frontend**:
   ```bash
   npm install -g serve
   ```

## Dọn dẹp dự án

Chúng tôi đã cung cấp script `cleanup_production.sh` để dọn dẹp dự án, loại bỏ các file không cần thiết và chuẩn bị cho môi trường production.

1. **Chạy script dọn dẹp**:
   ```bash
   ./cleanup_production.sh
   ```

Script này sẽ:
- Tạo bản sao lưu của dự án trước khi thực hiện các thay đổi
- Xóa các file test, debug và không cần thiết
- Xóa các script utility không cần cho production
- Xây dựng frontend trong chế độ production
- Chuẩn bị backend cho production

## Khởi động dự án

Sau khi dọn dẹp, bạn có thể sử dụng script `start_production.sh` để khởi động dự án trong môi trường production.

1. **Chạy script khởi động**:
   ```bash
   ./start_production.sh
   ```

Script này sẽ:
- Dừng các tiến trình đang chạy (nếu có)
- Khởi động backend với Gunicorn
- Khởi động frontend với Serve
- Hiển thị thông tin truy cập

## Cấu hình bổ sung

### Cấu hình tài khoản root

Tài khoản root mặc định:
- **Username**: root
- **Password**: FpT@707279-hCMcIty

Bạn nên thay đổi mật khẩu mặc định sau khi đăng nhập lần đầu.

### Cấu hình 2FA

Để tăng cường bảo mật, hãy thiết lập xác thực hai yếu tố (2FA) cho tài khoản root bằng công cụ database_tool.py:

```bash
cd backend
python database_tool.py setup-2fa
```

### Cấu hình port server

- Frontend mặc định chạy trên port 3000
- Backend mặc định chạy trên port 8000

Để thay đổi, chỉnh sửa trong các file cấu hình tương ứng hoặc sửa trực tiếp trong script `start_production.sh`.

## Xử lý sự cố

### Sự cố phổ biến

1. **Lỗi kết nối cơ sở dữ liệu**:
   - Kiểm tra cấu hình PostgreSQL trong file `.env`
   - Đảm bảo dịch vụ PostgreSQL đang chạy

2. **Lỗi khi khởi động frontend**:
   - Kiểm tra đã build frontend thành công chưa
   - Đảm bảo port 3000 không bị chiếm dụng

3. **Lỗi khi khởi động backend**:
   - Kiểm tra logs trong thư mục backend
   - Đảm bảo môi trường Python đã kích hoạt
   - Kiểm tra các phụ thuộc trong requirements.txt

### Các công cụ hỗ trợ

- **Database tool**: `python backend/database_tool.py`
- **Kiểm tra logs**: Logs Gunicorn nằm trong thư mục backend

---

Tài liệu này tạo bởi GitHub Copilot. Cập nhật lần cuối: $(date +"%d/%m/%Y").
