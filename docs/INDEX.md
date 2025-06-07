# Hệ thống quản lý người dùng - Tài liệu

## Giới thiệu
Đây là tài liệu tổng hợp cho hệ thống quản lý người dùng. Tài liệu này bao gồm các hướng dẫn triển khai, cấu hình bảo mật và xử lý sự cố.

## Scripts Mới Cho Production

Dự án cung cấp hai scripts chính để chuẩn bị và vận hành trong môi trường production:

1. **cleanup_production.sh**: Dọn dẹp dự án, loại bỏ các file không cần thiết, và chuẩn bị cho triển khai production
   ```bash
   ./cleanup_production.sh
   ```

2. **start_production.sh**: Khởi động ứng dụng trong môi trường production
   ```bash
   ./start_production.sh
   ```

## Tài Liệu Chính

### Triển Khai và Cài Đặt
- [Hướng Dẫn Nhanh: Triển Khai Production](QUICK_PRODUCTION_GUIDE.md): Tóm tắt các bước triển khai
- [Hướng Dẫn Triển Khai Production](PRODUCTION_DEPLOYMENT_GUIDE.md): Chi tiết đầy đủ về triển khai production
- [Hướng dẫn triển khai](guides/DEPLOYMENT_GUIDE.md): Hướng dẫn chung
- [Hướng dẫn thiết lập PostgreSQL](guides/POSTGRES_SETUP_GUIDE.md): Cấu hình PostgreSQL

### Bảo mật
- [Hướng dẫn xác thực bắt buộc 2FA](security/MANDATORY_2FA_VERIFICATION_GUIDE.md)
- [Hướng dẫn đăng nhập tài khoản Root](security/ROOT_USER_LOGIN_GUIDE.md)
- [Luồng xác thực 2FA cho tài khoản Root](security/ROOT_USER_2FA_FLOW.md)
- [Bảo mật tài khoản Root](security/ROOT_USER_SECURITY.md)

### Xử lý sự cố
- [Xử lý sự cố cơ sở dữ liệu](troubleshooting/DATABASE_TROUBLESHOOTING.md)
- [Xử lý sự cố JWT Token](troubleshooting/JWT_TOKEN_TROUBLESHOOTING.md)
- [Xử lý sự cố đăng nhập tài khoản Root](troubleshooting/ROOT_USER_LOGIN_TROUBLESHOOTING.md)
- [Xử lý sự cố tạo người dùng](troubleshooting/USER_CREATION_FIX.md)
- [Xử lý sự cố PostgreSQL trên macOS](troubleshooting/MACOS_POSTGRES_TROUBLESHOOTING.md)

### Sử Dụng và Quản Trị
- [Triển Khai Phân Quyền Dựa Trên Vai Trò](ROLE_BASED_ACCESS_IMPLEMENTATION.md)
- [Hướng Dẫn Nhập Người Dùng](USER_IMPORT_GUIDE.md)

## Công Cụ Quản Lý Database

Dự án cung cấp công cụ `database_tool.py` để quản lý và bảo trì cơ sở dữ liệu:

```bash
# Khởi động menu tương tác
python backend/database_tool.py

# Hoặc sử dụng các lệnh trực tiếp
python backend/database_tool.py init              # Khởi tạo cơ sở dữ liệu
python backend/database_tool.py create-root       # Tạo tài khoản root
python backend/database_tool.py setup-2fa         # Thiết lập 2FA cho tài khoản root
```

## Cấu trúc dự án
Cấu trúc dự án được tổ chức như sau:
- `backend/` - API và logic nghiệp vụ
- `frontend/` - Giao diện người dùng
- `docs/` - Tài liệu dự án

## Tài nguyên liên quan
- [README.md](/README.md) - Tổng quan về dự án
- [API Documentation](/backend/API_DOCS.md) - Tài liệu API
- [Công cụ quản lý database](/backend/DATABASE_TOOL_README.md) - Hướng dẫn sử dụng công cụ database

---

*Tài liệu này được cập nhật lần cuối ngày 12/05/2025*