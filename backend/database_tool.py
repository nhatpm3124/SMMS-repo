#!/usr/bin/env python3
# database_tool.py - Công cụ quản lý cơ sở dữ liệu tổng hợp

import os
import sys
import time
import argparse
import pyotp
import subprocess
import textwrap
import traceback  # Added import for traceback
import math  # Added import for pagination
from datetime import datetime

# Đảm bảo rằng đường dẫn hiện tại được thêm vào sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from app import create_app
    from app.models.models import User, db
    from app.models.student import Student
except ImportError as e:
    print(f"Lỗi: Không thể import các module cần thiết - {e}")
    print("Vui lòng đảm bảo bạn đang chạy script từ thư mục gốc của backend.")
    sys.exit(1)

# Màu sắc cho terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
 
def print_header(text):
    """In tiêu đề với định dạng"""
    width = 70
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * width}")
    print(f"{text.center(width)}")
    print(f"{'=' * width}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.ENDC}")
    
def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.ENDC}")

def clear_screen():
    """Xóa màn hình terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def confirm_action(message="Bạn có chắc chắn muốn thực hiện hành động này không?"):
    """Yêu cầu xác nhận từ người dùng"""
    response = input(f"{Colors.YELLOW}{message} (y/N): {Colors.ENDC}").lower().strip()
    return response == 'y'

# === CÁC CHỨC NĂNG QUẢN LÝ DATABASE ===

def init_database():
    """Khởi tạo cơ sở dữ liệu"""
    print_header("KHỞI TẠO CƠ SỞ DỮ LIỆU")
    
    if not confirm_action("Thao tác này sẽ tạo mới các bảng trong cơ sở dữ liệu. Tiếp tục?"):
        print_info("Đã hủy thao tác.")
        return

    try:
        app = create_app()
        with app.app_context():
            db.create_all()
            print_success("Đã khởi tạo cơ sở dữ liệu thành công.")
            
            # Kiểm tra xem đã có bản ghi nào chưa
            user_count = User.query.count()
            print_info(f"Số lượng người dùng hiện tại: {user_count}")
    except Exception as e:
        print_error(f"Lỗi khi khởi tạo cơ sở dữ liệu: {str(e)}")

def reset_database():
    """Xóa và tạo lại cơ sở dữ liệu"""
    print_header("XÓA VÀ TẠO LẠI CƠ SỞ DỮ LIỆU")
    
    warning_text = "CẢNH BÁO: Thao tác này sẽ XÓA TẤT CẢ DỮ LIỆU hiện có và tạo lại cấu trúc cơ sở dữ liệu!"
    print_warning(warning_text)
    
    if not confirm_action("Bạn có chắc chắn muốn tiếp tục không? Dữ liệu đã xóa không thể khôi phục!"):
        print_info("Đã hủy thao tác.")
        return
    
    if not confirm_action("Xác nhận lại lần cuối - tất cả dữ liệu sẽ bị mất!"):
        print_info("Đã hủy thao tác.")
        return
        
    try:
        app = create_app()
        with app.app_context():
            db.drop_all()
            print_info("Đã xóa tất cả bảng trong cơ sở dữ liệu.")
            
            db.create_all()
            print_success("Đã tạo lại cấu trúc cơ sở dữ liệu thành công.")
    except Exception as e:
        print_error(f"Lỗi khi reset cơ sở dữ liệu: {str(e)}")

def create_root_user(custom=False):
    """Tạo tài khoản root"""
    print_header("TẠO TÀI KHOẢN ROOT")
    
    if custom:
        print_info("Chế độ tạo tài khoản root với tùy chọn")
    else:
        print_info("Chế độ tạo tài khoản root với thông tin mặc định")
    
    try:
        app = create_app()
        with app.app_context():
            # Kiểm tra xem đã có tài khoản root chưa
            existing_root = User.query.filter_by(is_root=True).first()
            if (existing_root):
                print_warning(f"Đã tồn tại tài khoản root với username: {existing_root.username}")
                if not confirm_action("Bạn có muốn tạo thêm một tài khoản root khác không?"):
                    print_info("Đã hủy thao tác.")
                    return
            
            # Thiết lập thông tin cho tài khoản root
            if custom:
                username = input("Nhập tên đăng nhập (mặc định: root): ").strip() or "root"
                password = input("Nhập mật khẩu (mặc định: FpT@707279-hCMcIty): ").strip() or "FpT@707279-hCMcIty"
                email = input("Nhập email (mặc định: root@fpt.edu.vn): ").strip() or "root@fpt.edu.vn"
                fullName = input("Nhập họ tên (mặc định: System Root User): ").strip() or "System Root User"
                area = input("Nhập khu vực (mặc định: FPT HCM): ").strip() or "FPT HCM"
                house = input("Nhập cơ sở (mặc định: FPTU): ").strip() or "FPTU"
                phone = input("Nhập số điện thoại (mặc định: +840123456): ").strip() or "+840123456"
            else:
                username = "root"
                password = "FpT@707279-hCMcIty"
                email = "root@fpt.edu.vn"
                fullName = "System Root User"
                area = "FPT HCM"
                house = "FPTU"
                phone = "+840123456"
            
            # Tạo tài khoản root mới
            user = User(
                username=username,
                email=email,
                fullName=fullName,
                area=area,
                house=house,
                phone=phone,
                is_root=True,
                is_admin=True,
                role='root',
                two_factor_enabled=True,
                status="active"
            )
            user.set_password(password)
            
            # Thiết lập 2FA
            secret = user.setup_2fa()
            
            db.session.add(user)
            db.session.commit()
            
            print_success(f"Đã tạo tài khoản root thành công với username: {username}")
            
            # Hiển thị thông tin 2FA
            print_info("\nThông tin xác thực hai yếu tố (2FA):")
            print(f"Secret key: {secret}")
            print(f"URI: {user.get_2fa_uri(app_name='FPT System')}")
            
            # Tạo mã QR để quét
            try:
                import qrcode
                from PIL import Image
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(user.get_2fa_uri(app_name="FPT System"))
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                qr_file = os.path.join(current_dir, "root_2fa_qr.png")
                img.save(qr_file)
                
                print_success(f"Mã QR được lưu tại: {qr_file}")
                print_info("Quét mã QR này bằng ứng dụng Google Authenticator để thiết lập 2FA.")
            except ImportError:
                print_warning("Thư viện qrcode không khả dụng, không thể tạo mã QR.")
                print_info("Hãy nhập secret key trực tiếp vào ứng dụng xác thực.")
            
            # Tạo mã 2FA hiện tại
            totp = pyotp.TOTP(secret)
            current_token = totp.now()
            time_remaining = 30 - (int(time.time()) % 30)
            
            print_info(f"\nMã 2FA hiện tại: {current_token} (còn hiệu lực {time_remaining}s)")
                
    except Exception as e:
        print_error(f"Lỗi khi tạo tài khoản root: {str(e)}")
        import traceback
        traceback.print_exc()

def check_root_account():
    """Kiểm tra thông tin tài khoản root và trạng thái 2FA"""
    print_header("KIỂM TRA TÀI KHOẢN ROOT")
    
    try:
        app = create_app()
        with app.app_context():
            root_user = User.query.filter_by(is_root=True).first()
            
            if not root_user:
                print_warning("Không tìm thấy tài khoản root trong cơ sở dữ liệu.")
                if confirm_action("Bạn có muốn tạo tài khoản root mới không?"):
                    create_root_user()
                return
            
            print_info("Thông tin tài khoản root:")
            print(f"  - Username: {root_user.username}")
            print(f"  - Email: {root_user.email}")
            print(f"  - Họ tên: {root_user.fullName}")
            print(f"  - Khu vực: {root_user.area}")
            print(f"  - Cơ sở: {root_user.house}")
            print(f"  - SĐT: {root_user.phone}")
            print(f"  - Trạng thái: {root_user.status}")
            print(f"  - 2FA đã bật: {'Có' if root_user.two_factor_enabled else 'Không'}")
            print(f"  - 2FA đã thiết lập: {'Có' if root_user.two_factor_secret else 'Không'}")
            
            # Kiểm tra mật khẩu mặc định
            if root_user.check_password("FpT@707279-hCMcIty"):
                print_warning("Tài khoản root đang sử dụng mật khẩu mặc định.")
                print_info("Bạn nên thay đổi mật khẩu mặc định để tăng cường bảo mật.")
                if confirm_action("Bạn có muốn đổi mật khẩu ngay bây giờ không?"):
                    change_root_password()
            else:
                print_success("Tài khoản root đang sử dụng mật khẩu đã thay đổi.")
            
            # Kiểm tra và hiển thị mã 2FA hiện tại nếu có
            if root_user.two_factor_secret:
                if confirm_action("Bạn có muốn hiển thị mã 2FA hiện tại không?"):
                    get_current_2fa_token()
    
    except Exception as e:
        print_error(f"Lỗi khi kiểm tra tài khoản root: {str(e)}")

def get_current_2fa_token():
    """Lấy mã 2FA hiện tại cho tài khoản root"""
    print_header("MÃ XÁC THỰC HAI YẾU TỐ HIỆN TẠI")
    
    try:
        app = create_app()
        with app.app_context():
            root_user = User.query.filter_by(is_root=True).first()
            
            if not root_user:
                print_error("Không tìm thấy tài khoản root trong cơ sở dữ liệu.")
                return
                
            if not root_user.two_factor_secret:
                print_error("Tài khoản root chưa thiết lập 2FA.")
                if confirm_action("Bạn có muốn thiết lập 2FA cho tài khoản root không?"):
                    setup_2fa_for_root()
                return
            
            # Tạo mã TOTP
            totp = pyotp.TOTP(root_user.two_factor_secret)
            token = totp.now()
            
            # Tính thời gian còn lại
            time_remaining = 30 - (int(time.time()) % 30)
            
            print_info(f"Tài khoản: {root_user.username}")
            print_success(f"Mã 2FA hiện tại: {token}")
            print_info(f"Còn hiệu lực trong: {time_remaining} giây")
            
            # Đếm ngược
            if confirm_action("Bạn có muốn đợi mã tiếp theo không?"):
                print_info(f"Đợi {time_remaining} giây cho mã tiếp theo...")
                time.sleep(time_remaining)
                
                # Lấy mã mới
                token = totp.now()
                print_success(f"Mã 2FA mới: {token}")
                print_info("Mã này có hiệu lực trong 30 giây.")
    
    except Exception as e:
        print_error(f"Lỗi khi lấy mã 2FA: {str(e)}")

def setup_2fa_for_root():
    """Thiết lập 2FA cho tài khoản root"""
    print_header("THIẾT LẬP XÁC THỰC HAI YẾU TỐ CHO ROOT")
    
    try:
        app = create_app()
        with app.app_context():
            root_user = User.query.filter_by(is_root=True).first()
            
            if not root_user:
                print_error("Không tìm thấy tài khoản root trong cơ sở dữ liệu.")
                if confirm_action("Bạn có muốn tạo tài khoản root mới không?"):
                    create_root_user()
                return
            
            if root_user.two_factor_secret and not confirm_action(
                "Tài khoản root đã thiết lập 2FA. Bạn có muốn thiết lập lại không?"
            ):
                print_info("Đã hủy thao tác.")
                return
            
            # Thiết lập 2FA
            secret = root_user.setup_2fa()
            root_user.two_factor_enabled = True
            db.session.commit()
            
            print_success("Đã thiết lập 2FA thành công cho tài khoản root.")
            
            # Hiển thị thông tin 2FA
            print_info("\nThông tin xác thực hai yếu tố (2FA):")
            print(f"Secret key: {secret}")
            print(f"URI: {root_user.get_2fa_uri(app_name='FPT System')}")
            
            # Tạo mã QR để quét
            try:
                import qrcode
                from PIL import Image
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(root_user.get_2fa_uri(app_name="FPT System"))
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                qr_file = os.path.join(current_dir, "root_2fa_qr.png")
                img.save(qr_file)
                
                print_success(f"Mã QR được lưu tại: {qr_file}")
                print_info("Quét mã QR này bằng ứng dụng Google Authenticator để thiết lập 2FA.")
            except ImportError:
                print_warning("Thư viện qrcode không khả dụng, không thể tạo mã QR.")
                print_info("Hãy nhập secret key trực tiếp vào ứng dụng xác thực.")
            
            # Tạo mã 2FA hiện tại
            totp = pyotp.TOTP(secret)
            current_token = totp.now()
            time_remaining = 30 - (int(time.time()) % 30)
            
            print_info(f"\nMã 2FA hiện tại: {current_token} (còn hiệu lực {time_remaining}s)")
    
    except Exception as e:
        print_error(f"Lỗi khi thiết lập 2FA: {str(e)}")

def change_root_password():
    """Thay đổi mật khẩu tài khoản root"""
    print_header("THAY ĐỔI MẬT KHẨU TÀI KHOẢN ROOT")
    
    try:
        app = create_app()
        with app.app_context():
            root_user = User.query.filter_by(is_root=True).first()
            
            if not root_user:
                print_error("Không tìm thấy tài khoản root trong cơ sở dữ liệu.")
                return
            
            current_password = input("Nhập mật khẩu hiện tại: ")
            if not root_user.check_password(current_password):
                print_error("Mật khẩu hiện tại không đúng.")
                return
            
            new_password = input("Nhập mật khẩu mới: ")
            if not new_password:
                print_error("Mật khẩu không được để trống.")
                return
                
            confirm_password = input("Xác nhận mật khẩu mới: ")
            if new_password != confirm_password:
                print_error("Mật khẩu xác nhận không khớp.")
                return
            
            # Kiểm tra độ mạnh của mật khẩu
            if len(new_password) < 8:
                print_warning("Mật khẩu nên có ít nhất 8 ký tự.")
                if not confirm_action("Bạn vẫn muốn sử dụng mật khẩu này?"):
                    return
            
            # Cập nhật mật khẩu
            root_user.set_password(new_password)
            db.session.commit()
            
            print_success("Đã thay đổi mật khẩu thành công.")
    
    except Exception as e:
        print_error(f"Lỗi khi thay đổi mật khẩu: {str(e)}")

def verify_mandatory_2fa():
    """Kiểm tra xác thực 2FA bắt buộc cho tài khoản root"""
    print_header("KIỂM TRA XÁC THỰC 2FA BẮT BUỘC")
    
    try:
        app = create_app()
        with app.app_context():
            root_user = User.query.filter_by(is_root=True).first()
            
            if not root_user:
                print_error("Không tìm thấy tài khoản root trong cơ sở dữ liệu.")
                return
            
            print_info("Kiểm tra tài khoản root...")
            print(f"Username: {root_user.username}")
            print(f"2FA đã bật: {'Có' if root_user.two_factor_enabled else 'Không'}")
            print(f"2FA đã thiết lập: {'Có' if root_user.two_factor_secret else 'Không'}")
            
            if not root_user.two_factor_secret or not root_user.two_factor_enabled:
                print_warning("2FA chưa được thiết lập hoặc bật đầy đủ cho tài khoản root.")
                print_info("Tài khoản root cần phải có 2FA được bật và thiết lập.")
                return
            
            print_success("Tài khoản root đã thiết lập 2FA đúng cách.")
            print_info("\nĐang kiểm tra quy trình xác thực 2FA...")
            
            # Hiển thị mã 2FA hiện tại để kiểm tra
            get_current_2fa_token()
            
            print_info("\nCấu hình 2FA đã sẵn sàng. Tài khoản root sẽ yêu cầu mã 2FA khi đăng nhập.")
    
    except Exception as e:
        print_error(f"Lỗi khi kiểm tra 2FA bắt buộc: {str(e)}")

def generate_new_qr_code():
    """Tạo mã QR mới cho tài khoản root đã thiết lập 2FA"""
    print_header("TẠO MÃ QR MỚI CHO 2FA")
    
    try:
        app = create_app()
        with app.app_context():
            root_user = User.query.filter_by(is_root=True).first()
            
            if not root_user:
                print_error("Không tìm thấy tài khoản root trong cơ sở dữ liệu.")
                return
                
            if not root_user.two_factor_secret:
                print_error("Tài khoản root chưa thiết lập 2FA.")
                if confirm_action("Bạn có muốn thiết lập 2FA cho tài khoản root không?"):
                    setup_2fa_for_root()
                return
            
            # Tạo mã QR với secret hiện tại
            try:
                import qrcode
                from PIL import Image
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                totp_uri = root_user.get_2fa_uri(app_name="FPT System")
                qr.add_data(totp_uri)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                qr_file = os.path.join(current_dir, "root_2fa_qr.png")
                img.save(qr_file)
                
                print_success(f"Đã tạo mã QR mới tại: {qr_file}")
                print_info("Quét mã QR này bằng ứng dụng Google Authenticator.")
                print_info(f"Chú ý: Secret key không thay đổi, chỉ tạo lại mã QR: {root_user.two_factor_secret}")
                
                # Hiển thị thông tin hiện tại
                totp = pyotp.TOTP(root_user.two_factor_secret)
                current_token = totp.now()
                time_remaining = 30 - (int(time.time()) % 30)
                
                print_info(f"Mã 2FA hiện tại: {current_token} (còn hiệu lực {time_remaining}s)")
                
            except ImportError:
                print_error("Thư viện qrcode không khả dụng, không thể tạo mã QR.")
                print_info(f"URI cho thiết lập thủ công: {root_user.get_2fa_uri(app_name='FPT System')}")
    
    except Exception as e:
        print_error(f"Lỗi khi tạo mã QR: {str(e)}")

def run_database_migrations():
    """Chạy các migration cơ sở dữ liệu"""
    print_header("CHẠY MIGRATION CƠ SỞ DỮ LIỆU")
    
    try:
        # Chạy lệnh migration thông qua Flask CLI
        print_info("Đang chạy các migration...")
        
        flask_cmd = f"cd {current_dir} && FLASK_APP=run.py flask db upgrade"
        result = subprocess.run(flask_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Đã chạy migration thành công.")
            print_info("Kết quả:")
            print(result.stdout)
        else:
            print_error("Lỗi khi chạy migration.")
            print_info("Chi tiết lỗi:")
            print(result.stderr)
            
    except Exception as e:
        print_error(f"Lỗi khi chạy migration: {str(e)}")

def diagnose_database():
    """Chẩn đoán các vấn đề cơ sở dữ liệu"""
    print_header("CHẨN ĐOÁN CƠ SỞ DỮ LIỆU")
    
    try:
        app = create_app()
        with app.app_context():
            print_info("Đang kiểm tra kết nối cơ sở dữ liệu...")
            
            try:
                db.session.execute("SELECT 1")
                print_success("Kết nối cơ sở dữ liệu OK.")
            except Exception as e:
                print_error(f"Không thể kết nối đến cơ sở dữ liệu: {str(e)}")
                return
            
            print_info("Đang kiểm tra cấu trúc cơ sở dữ liệu...")
            
            # Kiểm tra các bảng
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print_info(f"Các bảng hiện có: {', '.join(tables)}")
            
            # Kiểm tra bảng User
            if 'user' not in [t.lower() for t in tables]:
                print_error("Bảng 'user' không tồn tại trong cơ sở dữ liệu.")
                if confirm_action("Bạn có muốn chạy migration để tạo bảng không?"):
                    run_database_migrations()
                return
            
            # Kiểm tra bảng Student
            if 'student' not in [t.lower() for t in tables]:
                print_error("Bảng 'student' không tồn tại trong cơ sở dữ liệu.")
                if confirm_action("Bạn có muốn chạy migration để tạo bảng không?"):
                    run_database_migrations()
                return
            
            # Kiểm tra số lượng người dùng
            user_count = User.query.count()
            print_info(f"Số lượng người dùng: {user_count}")
            
            # Kiểm tra số lượng sinh viên
            student_count = Student.query.count()
            print_info(f"Số lượng sinh viên: {student_count}")
            
            # Kiểm tra số lượng người dùng BroSis
            brosis_count = User.query.filter_by(role='brosis').count()
            print_info(f"Số lượng người dùng BroSis: {brosis_count}")
            
            # Kiểm tra tài khoản root
            root_count = User.query.filter_by(is_root=True).count()
            print_info(f"Số lượng tài khoản root: {root_count}")
            
            if root_count == 0:
                print_warning("Không có tài khoản root trong hệ thống.")
                if confirm_action("Bạn có muốn tạo tài khoản root không?"):
                    create_root_user()
            elif root_count > 1:
                print_warning(f"Có {root_count} tài khoản root trong hệ thống.")
                print_warning("Hệ thống nên chỉ có một tài khoản root duy nhất.")
                
                if confirm_action("Bạn có muốn xem danh sách các tài khoản root không?"):
                    root_users = User.query.filter_by(is_root=True).all()
                    for idx, user in enumerate(root_users, 1):
                        print(f"{idx}. Username: {user.username}, Email: {user.email}, ID: {user.id}")
            
            # Kiểm tra nếu còn User với role='brosis'
            if brosis_count > 0:
                print_warning(f"Có {brosis_count} người dùng với role='brosis' trong bảng User.")
                print_info("Những người dùng này nên được chuyển sang bảng Student.")
                if confirm_action("Bạn có muốn chuyển dữ liệu này sang bảng Student không?"):
                    migrate_users_to_students()
            
            print_success("Chẩn đoán cơ sở dữ liệu hoàn tất.")
    
    except Exception as e:
        print_error(f"Lỗi khi chẩn đoán cơ sở dữ liệu: {str(e)}")
        import traceback
        traceback.print_exc()

def backup_database():
    """Sao lưu cơ sở dữ liệu"""
    print_header("SAO LƯU CƠ SỞ DỮ LIỆU")
    
    try:
        app = create_app()
        config = app.config
        
        # Xác định loại cơ sở dữ liệu đang sử dụng
        db_uri = config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if 'postgresql' in db_uri:
            # Sao lưu PostgreSQL
            backup_dir = os.path.join(current_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(
                backup_dir, 
                f"postgres_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            )
            
            # Lấy thông tin kết nối từ URI
            from urllib.parse import urlparse
            result = urlparse(db_uri)
            dbname = result.path[1:]  # Bỏ dấu / ở đầu
            user = result.username
            password = result.password
            host = result.hostname
            port = result.port or 5432
            
            # Tạo biến môi trường tạm thời cho mật khẩu
            os.environ['PGPASSWORD'] = password
            
            pg_dump_cmd = f"pg_dump -h {host} -p {port} -U {user} -F c -b -v -f {backup_file} {dbname}"
            result = subprocess.run(pg_dump_cmd, shell=True, capture_output=True, text=True)
            
            # Xóa biến môi trường
            os.environ.pop('PGPASSWORD', None)
            
            if result.returncode == 0:
                print_success(f"Đã sao lưu cơ sở dữ liệu PostgreSQL vào: {backup_file}")
            else:
                print_error("Lỗi khi sao lưu PostgreSQL.")
                print_info("Chi tiết lỗi:")
                print(result.stderr)
        
        else:
            print_error(f"Không hỗ trợ sao lưu cho loại cơ sở dữ liệu này: {db_uri}")
    
    except Exception as e:
        print_error(f"Lỗi khi sao lưu cơ sở dữ liệu: {str(e)}")
        import traceback
        traceback.print_exc()

# === HÀM HIỂN THỊ MENU ===

def show_menu():
    """Hiển thị menu tương tác"""
    while True:
        clear_screen()
        print_header("CÔNG CỤ QUẢN LÝ CƠ SỞ DỮ LIỆU")
        
        print(f"{Colors.BLUE}[ THIẾT LẬP CƠ SỞ DỮ LIỆU ]{Colors.ENDC}")
        print(" 1. Khởi tạo cơ sở dữ liệu")
        print(" 2. Reset cơ sở dữ liệu (xóa và tạo lại)")
        print(" 3. Chạy migrations")
        print(" 4. Chẩn đoán cơ sở dữ liệu")
        print(" 5. Sao lưu cơ sở dữ liệu")
        
        print(f"\n{Colors.BLUE}[ QUẢN LÝ TÀI KHOẢN ROOT ]{Colors.ENDC}")
        print(" 6. Tạo tài khoản root (cấu hình mặc định)")
        print(" 7. Tạo tài khoản root tùy chỉnh")
        print(" 8. Kiểm tra tài khoản root")
        print(" 9. Thay đổi mật khẩu root")
        
        print(f"\n{Colors.BLUE}[ XÁC THỰC HAI YẾU TỐ (2FA) ]{Colors.ENDC}")
        print("10. Thiết lập 2FA cho tài khoản root")
        print("11. Lấy mã 2FA hiện tại")
        print("12. Kiểm tra tính bắt buộc của 2FA")
        print("13. Tạo mã QR mới cho 2FA hiện tại")
        
        print(f"\n{Colors.BLUE}[ QUẢN LÝ SINH VIÊN ]{Colors.ENDC}")
        print("14. Di chuyển sinh viên từ User sang Student")
        print("15. Thống kê dữ liệu sinh viên")
        print("16. Xóa tất cả sinh viên")
        
        print(f"\n{Colors.RED}0. Thoát{Colors.ENDC}")
        
        choice = input(f"\n{Colors.GREEN}Chọn một tùy chọn (0-16): {Colors.ENDC}")
        
        if choice == '0':
            break
        elif choice == '1':
            init_database()
        elif choice == '2':
            reset_database()
        elif choice == '3':
            run_database_migrations()
        elif choice == '4':
            diagnose_database()
        elif choice == '5':
            backup_database()
        elif choice == '6':
            create_root_user(custom=False)
        elif choice == '7':
            create_root_user(custom=True)
        elif choice == '8':
            check_root_account()
        elif choice == '9':
            change_root_password()
        elif choice == '10':
            setup_2fa_for_root()
        elif choice == '11':
            get_current_2fa_token()
        elif choice == '12':
            verify_mandatory_2fa()
        elif choice == '13':
            generate_new_qr_code()
        elif choice == '14':
            migrate_users_to_students()
        elif choice == '15':
            show_student_stats()
        elif choice == '16':
            delete_all_students()
        else:
            print_warning("Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        
        input(f"\n{Colors.YELLOW}Nhấn Enter để tiếp tục...{Colors.ENDC}")

# === XỬ LÝ THAM SỐ DÒNG LỆNH ===

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Công cụ quản lý cơ sở dữ liệu tổng hợp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Ví dụ sử dụng:
          database_tool.py                   # Chạy giao diện menu tương tác
          database_tool.py init              # Khởi tạo cơ sở dữ liệu
          database_tool.py create-root       # Tạo tài khoản root mặc định
          database_tool.py setup-2fa         # Thiết lập 2FA cho tài khoản root
          database_tool.py migrate-students  # Di chuyển dữ liệu sinh viên
        """)
    )
    
    parser.add_argument('action', nargs='?', default='menu',
                        choices=[
                            'menu', 'init', 'reset', 'migrate', 'diagnose', 'backup',
                            'create-root', 'custom-root', 'check-root', 'change-password',
                            'setup-2fa', 'get-2fa-token', 'verify-2fa', 'generate-qr',
                            'migrate-students', 'student-stats', 'delete-students'
                        ],
                        help='Hành động cần thực hiện')
    
    return parser.parse_args()

# === CHỨC NĂNG QUẢN LÝ SINH VIÊN ===

def migrate_users_to_students():
    """Di chuyển dữ liệu sinh viên từ User sang Student"""
    print_header("DI CHUYỂN DỮ LIỆU SINH VIÊN")
    
    try:
        app = create_app()
        with app.app_context():
            # Kiểm tra xem bảng Student đã tồn tại chưa
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'student' not in [t.lower() for t in tables]:
                print_error("Bảng Student chưa được tạo trong cơ sở dữ liệu.")
                if confirm_action("Bạn có muốn chạy migration để tạo bảng Student không?"):
                    run_database_migrations()
                    print_info("Vui lòng chạy lại chức năng này sau khi migration hoàn tất.")
                return
            
            # Đếm số lượng User có role='brosis' để di chuyển
            brosis_users = User.query.filter_by(role='brosis').all()
            if not brosis_users:
                print_warning("Không tìm thấy dữ liệu sinh viên nào trong bảng User để di chuyển.")
                return
            
            print_info(f"Tìm thấy {len(brosis_users)} người dùng role='brosis' để di chuyển sang Student.")
            
            if not confirm_action("Bạn có chắc chắn muốn chuyển dữ liệu sinh viên từ User sang Student không?"):
                print_info("Đã hủy thao tác.")
                return
            
            # Tạo Student record cho mỗi User có role='brosis'
            created_count = 0
            skipped_count = 0
            error_count = 0
            
            for user in brosis_users:
                try:
                    # Kiểm tra xem studentId có tồn tại không
                    if not user.studentId:
                        print_warning(f"Bỏ qua user {user.username} do không có studentId.")
                        skipped_count += 1
                        continue
                    
                    # Kiểm tra xem Student với studentId này đã tồn tại chưa
                    existing_student = Student.query.filter_by(studentId=user.studentId).first()
                    if existing_student:
                        print_warning(f"Sinh viên với studentId={user.studentId} đã tồn tại trong bảng Student.")
                        skipped_count += 1
                        continue
                    
                    # Tạo đối tượng Student mới
                    student = Student(
                        studentId=user.studentId,
                        fullName=user.fullName,
                        email=user.email,
                        phone=user.phone,
                        address="",  # Thông tin địa chỉ không có trong User
                        status=user.status
                    )
                    
                    db.session.add(student)
                    db.session.commit()
                    created_count += 1
                    
                    print_success(f"Đã tạo Student: {student.fullName} (ID: {student.studentId})")
                    
                except Exception as e:
                    print_error(f"Lỗi khi xử lý user {user.username}: {str(e)}")
                    error_count += 1
                    db.session.rollback()
            
            # Hiển thị thống kê
            print_info("\nKết quả chuyển đổi:")
            print(f"- Tổng số bản ghi xử lý: {len(brosis_users)}")
            print(f"- Đã tạo thành công: {created_count}")
            print(f"- Đã bỏ qua: {skipped_count}")
            print(f"- Lỗi: {error_count}")
            
            # Hỏi người dùng có muốn xóa các User role='brosis' không
            if created_count > 0 and confirm_action("Bạn có muốn xóa các User có role='brosis' không? Các sinh viên sẽ KHÔNG thể đăng nhập."):
                if confirm_action("XÁC NHẬN: Các User với role='brosis' sẽ bị xóa khỏi hệ thống!"):
                    try:
                        deleted_count = 0
                        for user in brosis_users:
                            db.session.delete(user)
                            deleted_count += 1
                        
                        db.session.commit()
                        print_success(f"Đã xóa {deleted_count} User với role='brosis'.")
                    except Exception as e:
                        print_error(f"Lỗi khi xóa User: {str(e)}")
                        db.session.rollback()
                else:
                    print_info("Đã hủy thao tác xóa.")
            
            print_info("\nQuá trình di chuyển dữ liệu sinh viên đã hoàn tất.")
    
    except Exception as e:
        print_error(f"Lỗi khi di chuyển dữ liệu sinh viên: {str(e)}")
        import traceback
        traceback.print_exc()

def show_student_stats():
    """Hiển thị thống kê dữ liệu sinh viên"""
    print_header("THỐNG KÊ DỮ LIỆU SINH VIÊN")
    
    try:
        app = create_app()
        with app.app_context():
            # Kiểm tra xem bảng Student đã tồn tại chưa
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'student' not in [t.lower() for t in tables]:
                print_error("Bảng Student chưa được tạo trong cơ sở dữ liệu.")
                return
            
            # Thống kê tổng số sinh viên
            total_students = Student.query.count()
            print_info(f"Tổng số sinh viên: {total_students}")
            
            # Thống kê theo trạng thái
            active_students = Student.query.filter_by(status='active').count()
            inactive_students = Student.query.filter_by(status='inactive').count()
            print_info(f"Sinh viên đang hoạt động: {active_students}")
            print_info(f"Sinh viên không hoạt động: {inactive_students}")
            
            # Thống kê sinh viên có email
            has_email = Student.query.filter(Student.email.isnot(None), Student.email != '').count()
            print_info(f"Sinh viên có email: {has_email}")
            
            # Thống kê sinh viên có số điện thoại
            has_phone = Student.query.filter(Student.phone.isnot(None), Student.phone != '').count()
            print_info(f"Sinh viên có số điện thoại: {has_phone}")
            
            # Hiển thị 5 sinh viên mới nhất
            print_info("\n5 sinh viên được thêm gần đây nhất:")
            recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
            
            if recent_students:
                for idx, student in enumerate(recent_students, 1):
                    print(f"{idx}. {student.fullName} (ID: {student.studentId}) - {student.created_at.strftime('%d-%m-%Y %H:%M')}")
            else:
                print_warning("Không có dữ liệu sinh viên nào.")
            
            # Kiểm tra dữ liệu User cũ
            old_brosis_count = User.query.filter_by(role='brosis').count()
            if old_brosis_count > 0:
                print_warning(f"\nVẫn còn {old_brosis_count} người dùng với role='brosis' trong bảng User.")
                if confirm_action("Bạn có muốn di chuyển dữ liệu này sang bảng Student không?"):
                    migrate_users_to_students()
    
    except Exception as e:
        print_error(f"Lỗi khi hiển thị thống kê sinh viên: {str(e)}")

def delete_all_students():
    """Xóa tất cả dữ liệu sinh viên"""
    print_header("XÓA TẤT CẢ DỮ LIỆU SINH VIÊN")
    
    try:
        app = create_app()
        with app.app_context():
            # Đếm số lượng sinh viên
            student_count = Student.query.count()
            
            if student_count == 0:
                print_warning("Không có dữ liệu sinh viên nào để xóa.")
                return
            
            print_warning(f"Thao tác này sẽ XÓA TẤT CẢ {student_count} sinh viên khỏi cơ sở dữ liệu!")
            print_warning("Dữ liệu đã xóa KHÔNG THỂ khôi phục.")
            
            if not confirm_action("Bạn có chắc chắn muốn xóa tất cả dữ liệu sinh viên không?"):
                print_info("Đã hủy thao tác.")
                return
            
            if not confirm_action("XÁC NHẬN LẦN CUỐI: Tất cả dữ liệu sinh viên sẽ bị mất vĩnh viễn!"):
                print_info("Đã hủy thao tác.")
                return
            
            # Xóa tất cả sinh viên
            Student.query.delete()
            db.session.commit()
            
            print_success(f"Đã xóa tất cả {student_count} sinh viên khỏi cơ sở dữ liệu.")
    
    except Exception as e:
        print_error(f"Lỗi khi xóa dữ liệu sinh viên: {str(e)}")
        db.session.rollback()

# === CHƯƠNG TRÌNH CHÍNH ===

if __name__ == "__main__":
    try:
        args = parse_arguments()
        
        if args.action == 'menu':
            show_menu()
        elif args.action == 'init':
            init_database()
        elif args.action == 'reset':
            reset_database()
        elif args.action == 'migrate':
            run_database_migrations()
        elif args.action == 'diagnose':
            diagnose_database()
        elif args.action == 'backup':
            backup_database()
        elif args.action == 'create-root':
            create_root_user(custom=False)
        elif args.action == 'custom-root':
            create_root_user(custom=True)
        elif args.action == 'check-root':
            check_root_account()
        elif args.action == 'change-password':
            change_root_password()
        elif args.action == 'setup-2fa':
            setup_2fa_for_root()
        elif args.action == 'get-2fa-token':
            get_current_2fa_token()
        elif args.action == 'verify-2fa':
            verify_mandatory_2fa()
        elif args.action == 'generate-qr':
            generate_new_qr_code()
        elif args.action == 'migrate-students':
            migrate_users_to_students()
        elif args.action == 'student-stats':
            show_student_stats()
        elif args.action == 'delete-students':
            delete_all_students()
    
    except KeyboardInterrupt:
        print_info("\nĐã hủy thao tác.")
    except Exception as e:
        print_error(f"Lỗi không xác định: {str(e)}")
        import traceback
        traceback.print_exc()
