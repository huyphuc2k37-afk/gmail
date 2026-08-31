# Gmail QR Investigation

Điều tra tại sao Google hiển thị QR code bắt buộc quét b�ng điện thoại khi đăng ký Gmail.

**Xem chi tiết quy trình + phân tích công nghệ:** [PROCESS.md](./PROCESS.md)

## Files
- `PROCESS.md` — Toàn bộ quy trình đã reproduce và phân tích kỹ thuật
- `gmail_interactive.py` — Script Playwright Python để reproduce
- `investigation/` — Log + screenshots từ các lần chạy

## Chạy nhanh
```powershell
cd "c:\Users\Admin\Documents\Gmail"
$env:PYTHONIOENCODING="utf-8"
python -X utf8 gmail_interactive.py
```
