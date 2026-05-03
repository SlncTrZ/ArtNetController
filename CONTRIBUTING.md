# Contributing to DMX Master LTS

Cảm ơn bạn đã quan tâm đến dự án DMX Master LTS! Tài liệu này hướng dẫn cách đóng góp cho dự án.

## Yêu cầu

- Python 3.13+
- Git
- PyQt6 (cho GUI development)

## Thiết lập môi trường phát triển

```bash
# Clone repository
git clone https://github.com/truongcongdinh97/DMX-Master.git
cd DMX-Master

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy tests để xác nhận setup
python -m pytest tests/ -v
```

## Quy trình phát triển

### 1. Tạo Branch

```bash
git checkout -b feature/ten-feature
# hoặc
git checkout -b fix/ten-bug-fix
```

### 2. Thực hiện thay đổi

- Tuân theo code style hiện có (PEP 8, type hints)
- Viết tests cho tính năng mới
- Cập nhật documentation nếu cần

### 3. Kiểm tra chất lượng

```bash
# Chạy tất cả tests
python -m pytest tests/ -v

# Kiểm tra code style (nếu có ruff/flake8)
ruff check src/
```

### 4. Commit & Push

```bash
git add .
git commit -m "feat: mô tả ngắn gọn"
git push origin feature/ten-feature
```

### 5. Tạo Pull Request

- Mô tả rõ ràng về thay đổi
- Liên kết đến issue nếu có
- Đảm bảo CI pass

## Commit Convention

Sử dụng [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Mô tả |
|--------|--------|
| `feat:` | Tính năng mới |
| `fix:` | Sửa bug |
| `docs:` | Thay đổi documentation |
| `style:` | Format code (không ảnh hưởng logic) |
| `refactor:` | Refactor code |
| `test:` | Thêm/sửa tests |
| `chore:` | Build, CI, dependencies |

## Báo cáo lỗi

Sử dụng [GitHub Issues](https://github.com/truongcongdinh97/DMX-Master/issues) với template:

- **Mô tả**: Vấn đề là gì?
- **Steps to reproduce**: Các bước tái hiện
- **Expected behavior**: Mong đợi gì?
- **Actual behavior**: Thực tế xảy ra gì?
- **Environment**: OS, Python version, version dự án

## Giấy phép

Bằng cách đóng góp, bạn đồng ý rằng các contribution của bạn sẽ được cấp phép theo giấy phép của dự án.
