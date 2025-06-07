# Hướng Dẫn Nhanh: Triển Khai Production

Tài liệu này cung cấp hướng dẫn nhanh để dọn dẹp dự án và triển khai trong môi trường production. Đây là tóm tắt các bước từ [Hướng Dẫn Triển Khai Production](PRODUCTION_DEPLOYMENT_GUIDE.md) chi tiết.

## Các Bước Triển Khai

### 1. Dọn dẹp dự án

Chạy script dọn dẹp để loại bỏ các file test, debug và không cần thiết:

```bash
./cleanup_production.sh
```

Script này sẽ:
- Tạo bản sao lưu của dự án
- Xóa các file test và debug
- Xóa các script không cần thiết
- Xây dựng frontend trong chế độ production
- Cài đặt các phụ thuộc cần thiết cho backend

### 2. Xác minh sự sẵn sàng

Kiểm tra dự án để đảm bảo tất cả đã sẵn sàng cho production:

```bash
./verify_production_readiness.sh
```

Script này sẽ:
- Kiểm tra các file không cần thiết còn sót lại
- Kiểm tra các file cần thiết cho production
- Kiểm tra cấu hình backend
- Kiểm tra build frontend
- Kiểm tra cấu hình cơ sở dữ liệu

### 3. Khởi động ứng dụng

Khởi động ứng dụng trong môi trường production:

```bash
./start_production.sh
```

Script này sẽ:
- Dừng các tiến trình đang chạy (nếu có)
- Khởi động backend với Gunicorn
- Khởi động frontend với Serve
- Hiển thị thông tin truy cập

## Xác thực và Tài Khoản Root

Tài khoản root mặc định có thông tin đăng nhập:
- **Username**: root
- **Password**: FpT@707279-hCMcIty

Bạn nên thay đổi mật khẩu mặc định sau khi đăng nhập lần đầu.

Để thiết lập 2FA cho tài khoản root:

```bash
cd backend
python database_tool.py setup-2fa
```

## Xử Lý Sự Cố

Các sự cố phổ biến và giải pháp:

1. **Lỗi kết nối cơ sở dữ liệu**: 
   - Kiểm tra file `.env` trong thư mục backend
   - Đảm bảo dịch vụ PostgreSQL đang chạy

2. **Lỗi khi khởi động frontend**:
   - Chạy lại build: `cd frontend && npm run build`
   - Kiểm tra port có bị chiếm dụng không

3. **Lỗi khi khởi động backend**:
   - Kiểm tra logs: `cd backend && cat app.log`
   - Kiểm tra cài đặt Gunicorn

## Thông Tin Thêm

Để được hướng dẫn chi tiết hơn, tham khảo:
- [Hướng Dẫn Triển Khai Production](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Xử Lý Sự Cố Cơ Sở Dữ Liệu](troubleshooting/DATABASE_TROUBLESHOOTING.md)

---

*Hướng dẫn này được tạo ngày 12/05/2025*
