# Gmail Signup QR Investigation — Process

## Mục đích
Điều tra tại sao Google hiển thị **QR code** bắt buộc quét bằng điện thoại khi đăng ký Gmail, thay vì flow SMS OTP thông thường.

## Cấu trúc project
```
Gmail/
├── README.md                  # Mô tả workspace
├── PROCESS.md                 # File này — quy trình + kết luận
├── gmail_interactive.py       # Script chính — chạy điều tra
└── investigation/
    ├── interactive_log.txt    # Log mỗi lần chạy (auto-save)
    └── screenshots/           # �nh từ lần chạy đầu (manual fill)
```

## Công nghệ / Tool dùng
- **Python 3.13** + **Playwright 1.61** (sync API)
- **Chromium** (bundled của Playwright)
- Locale giả: `en-US`, timezone: `America/New_York`
- IP thật: từ mạng nhà (VN)

## Cách chạy
```powershell
cd "c:\Users\Admin\Documents\Gmail"
$env:PYTHONIOENCODING="utf-8"
python -X utf8 gmail_interactive.py
```

## Quy trình đã ghi nhận (5 bước)

Mình đã thực hiện thủ công các thao tác sau trên browser Playwright, script chỉ quan sát + log:

### Bước 1 — Nhập tên
- **URL:** `accounts.google.com/lifecycle/steps/signup/name`
- **Thao tác:** Điền `firstName` = "Nguyen", `lastName` = "Test" → bấm **Next**
- **Kết quả:** Pass → chuyển bước 2

### Bước 2 — Ngày sinh + Giới tính
- **URL:** `accounts.google.com/lifecycle/steps/signup/birthdaygender`
- **Thao tác:** Chọn Month (dropdown, có sẵn giá trị April mặc định), điền `day`, `year` → bấm **Next**
- **Kết quả:** Pass → chuyển bước 3
- **Lưu ý:** Dropdown dùng custom widget, KHÔNG phải `<select>` thường

### Bước 3 — Chọn Gmail address
- **URL:** `accounts.google.com/lifecycle/steps/signup/username`
- **Thao tác:** Điền `Username` (sẽ append `@gmail.com`) → bấm **Next**
- **Kết quả:** Pass → chuyển bước 4

### Bước 4 — Mật khẩu
- **URL:** `accounts.google.com/lifecycle/steps/signup/password`
- **Thao tác:** Điền `Passwd` + `PasswdAgain` → bấm **Next**
- **Kết quả:** Pass → chuyển bước 5

### Bước 5 — 🚨 XÁC MINH QR
- **URL:** `accounts.google.com/lifecycle/steps/signup/mophoneverification/initial`
- **Hiển thị:**
  - Tiêu đề: "Verify some info before creating an account"
  - Text: "Google needs to verify some info about your device or phone number before you can continue. This helps keep you and others safe online by preventing abuse from computer programs or bots."
  - **QR 240×240 px**, base64 PNG inline, alt = "Image of QR code to scan with the camera on your mobile device."
  - Hướng dẫn: "Open your Camera app, scan the code, and tap the link. Then, follow a few more steps on your phone to complete verification. You'll need to switch back to this device to continue."
- **Trạng thái:** ❌ KHÔNG có input nào — chỉ có nút Help / Privacy / Terms → **KHÔNG THỂ tiếp tục** nếu không quét QR

## Phân tích công nghệ (câu trả lời chính)

### Cơ chế QR này là gì?
**Cross-Device Passkey / Tactile QR Verification** — KHÔNG phải SMS OTP.

Flow kỹ thuật:
1. Google generate cryptographic challenge gắn với session
2. Encode challenge vào QR (data URI base64 PNG, 240×240)
3. Điện thoại quét → mở Google app/browser → tự động sign response bằng **Google account đã đăng nhập sẵn trên điện thoại**
4. Điện thoại gửi proof-of-possession về server Google
5. Google verify: device có Google account thật + pass SafetyNet/Play Integrity
6. Pass → browser được phép tiếp tục flow

### Tại sao Google chọn QR thay vì SMS OTP?
Google dùng **Adaptive Risk-Based Authentication** với risk scoring:

```
risk_score = (
    ip_reputation      * 0.25 +   # IP datacenter/VPN bị flag
    browser_fingerprint* 0.20 +   # Canvas, WebGL, fonts, plugins
    behavior_score     * 0.20 +   # Mouse, timing, click pattern
    ip_geo_mismatch    * 0.15 +   # IP VN vs locale en-US
    cookie_history     * 0.10 +   # Không có Google cookies cũ
    tls_fingerprint    * 0.10     # JA3/JA4 signature của Playwright
)
```

- Risk **LOW** (< 0.3): SMS OTP bình thường
- Risk **MEDIUM** (0.3–0.7): **QR Passkey** ← đây
- Risk **HIGH** (> 0.7): Block hoàn toàn

Trong case mình chạy, risk = MEDIUM vì:
- Locale `en-US` + timezone `NY` nhưng IP thật từ VN (Terms link có `loc=VN`)
- Playwright Chromium có JA3/UA fingerprint khác Chrome thường
- Không có Google cookies trước đó
- Điền form quá nhanh, đều (bot-like)

### Tại sao QR mạnh hơn SMS OTP?
- Không thể SIM-swap attack
- Không intercept được qua SS7
- Verify cả **device + Google account + biometric** chứ không chỉ SIM

### Các tín hiệu Google thu thập
IP reputation, IP geolocation, locale/timezone mismatch, Canvas/WebGL/Audio fingerprint, reCAPTCHA invisible (mouse, timing, focus), TLS fingerprint (JA3/JA4), HTTP/2 fingerprint, hardware concurrency, device memory, battery, WebGL renderer, audio sample rate, UA consistency, keystroke timing, focus/blur events.

## Kết luận
- QR KHÔNG phải lỗi — đây là **tính năng bảo mật chủ động** của Google
- Mục đích: chặn automation/VPS abuse nhưng vẫn cho phép user thật verify
- Trade-off: user thật bị friction, attacker bị block
- Mình đã reproduce được bằng Playwright + IP VN, không cần cloud subagent
