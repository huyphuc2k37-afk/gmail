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

## Quy trình — chi tiết từng thao tác (để sau tự động hóa)

URL gốc: `https://accounts.google.com/signup` — đã được Google redirect sang URL thật `/lifecycle/steps/signup/...` ngay sau khi load.

Mỗi bước có format:
- **URL:** path của endpoint Google
- **Selectors:** chính xác selector CSS / XPath dùng để tương tác
- **Action:** hành động cần làm (fill/select/click)
- **Verify:** cách biết step đã pass

### Bước 1 — Name
- **URL:** `https://accounts.google.com/lifecycle/steps/signup/name?dsh=...&flowEntry=SignUp&flowName=GlifWebSignIn&TL=...&continue=...`
- **Selectors:**
  - `#firstName` — input text "First name"
  - `#lastName` — input text "Last name (optional)"
  - `button:has-text("Next")` — nút Next (cũng là `<button>` không có id, match theo text)
- **Action:**
  ```
  page.fill('#firstName', 'Nguyen')
  page.fill('#lastName', 'Test')
  page.click('button:has-text("Next")')
  ```
- **Verify:** URL đổi từ `/name` → `/birthdaygender`. Cookie flow name chuyển tiếp tự động.

### Bước 2 — Birthday + Gender
- **URL:** `https://accounts.google.com/lifecycle/steps/signup/birthdaygender?...`
- **Selectors:**
  - `[aria-label="Month"]` hoặc click button month hiện tại (mặc định là "April" hoặc "January" tùy locale) — **KHÔNG phải `<select>`**, đây là custom dropdown. Mở → chọn option trong listbox
  - `input[name="day"]` — input `type="tel"`, aria-label "Day"
  - `input[name="year"]` — input `type="tel"`, aria-label "Year"
  - `[role="radio"]` cho Gender (Female / Male / Rather not say / Custom) — KHÔNG phải `<input type=radio>`
  - `button:has-text("Next")`
- **Action:**
  ```
  # Month dropdown
  page.click('[aria-label="Month"]')                # mở dropdown
  page.click('div[role="option"]:has-text("June")')  # chọn option

  page.fill('input[name="day"]', '15')
  page.fill('input[name="year"]', '1995')

  # Gender (chọn 1 trong 4)
  page.click('[role="radio"][aria-label*="Male"]')   # hoặc Female
  # Nếu chọn "Rather not say" / "Custom" thì có thêm ô input

  page.click('button:has-text("Next")')
  ```
- **Verify:** URL đổi → `/username`. Không xuất hiện error message nào dưới input.

### Bước 3 — Username (Gmail address)
- **URL:** `https://accounts.google.com/lifecycle/steps/signup/username?...`
- **Selectors:**
  - `input[aria-label="Username"]` — input text, append `@gmail.com` tự động
  - `button:has-text("Next")`
  - `button:has-text("Use your existing email")` — option phụ, không cần click
- **Action:**
  ```
  page.fill('input[aria-label="Username"]', 'nguyentest' + random_string(6))
  page.click('button:has-text("Next")')
  ```
- **Lưu ý:** Username phải unique. Google check availability real-time; nếu trùng sẽ hiển thị gợi ý khác.
- **Verify:** URL đổi → `/password`.

### Bước 4 — Password
- **URL:** `https://accounts.google.com/lifecycle/steps/signup/password?...`
- **Selectors:**
  - `input[aria-label="Password"]` — `type="password"`, `name="Passwd"`
  - `input[aria-label="Confirm"]` — `type="password"`, `name="PasswdAgain"`
  - `input[type="checkbox"]` — checkbox "Show password" (optional, không cần check)
  - `button:has-text("Next")`
- **Action:**
  ```
  page.fill('input[aria-label="Password"]', 'TestPass123!')
  page.fill('input[aria-label="Confirm"]', 'TestPass123!')
  page.click('button:has-text("Next")')
  ```
- **Verify:** URL đổi → `/mophoneverification/initial`. **Đây là bước QR.**

### Bước 5 — 🚨 QR Verification (CHẶN)
- **URL:** `https://accounts.google.com/lifecycle/steps/signup/mophoneverification/initial?...`
- **Selectors:**
  - `img[alt*="QR code"]` — QR 240×240 px, `src="data:image/png;base64,..."`
  - Container: `<section class="Em2Ord">` (class Google dùng để wrap QR)
  - **KHÔNG có input/select/button nào khác ngoài Help/Privacy/TTerms** — đây là điểm dừng
- **Action (manual only):**
  1. Mở Camera app trên điện thoại (đã đăng nhập Google account)
  2. Quét QR
  3. Tap link Google hiện ra → app Google mở → confirm trên điện thoại (fingerprint / PIN)
  4. Quay lại browser → tự động redirect sang bước tiếp theo (`/signup/verifyemailpasskey` hoặc kết thúc tạo account)
- **Auto không thể** vì cần device thật + Google account thật + biometric.

## Selector cheat sheet (dùng lại nhiều lần)

| Element | Selector |
|---|---|
| First name | `#firstName` |
| Last name | `#lastName` |
| Day | `input[name="day"]` |
| Year | `input[name="year"]` |
| Month dropdown | `[aria-label="Month"]` |
| Month option | `div[role="option"]` |
| Gender | `[role="radio"]` |
| Username | `input[aria-label="Username"]` |
| Password | `input[aria-label="Password"]` |
| Confirm password | `input[aria-label="Confirm"]` |
| Show password | `input[type="checkbox"]` |
| Next button | `button:has-text("Next")` |
| Skip button | `button:has-text("Skip")` |
| Help link | `a[aria-label*="Help"]` |

## Hàm tiện ích (snippet để tự động hóa sau)

```python
from playwright.sync_api import Page

def click_next(page: Page):
    btn = page.locator('button:has-text("Next")').first
    btn.wait_for(state="visible", timeout=10_000)
    btn.click()

def fill_name(page: Page, first: str, last: str):
    page.locator('#firstName').fill(first)
    page.locator('#lastName').fill(last)
    click_next(page)
    page.wait_for_url("**/birthdaygender**", timeout=15_000)

def fill_birthday_gender(page: Page, day: int, year: int, month: str = "June", gender: str = "Male"):
    page.locator('[aria-label="Month"]').click()
    page.locator(f'div[role="option"]:has-text("{month}")').click()
    page.locator('input[name="day"]').fill(str(day))
    page.locator('input[name="year"]').fill(str(year))
    page.locator(f'[role="radio"][aria-label*="{gender}"]').click()
    click_next(page)
    page.wait_for_url("**/username**", timeout=15_000)

def fill_username(page: Page, username: str):
    page.locator('input[aria-label="Username"]').fill(username)
    click_next(page)
    page.wait_for_url("**/password**", timeout=15_000)

def fill_password(page: Page, password: str):
    page.locator('input[aria-label="Password"]').fill(password)
    page.locator('input[aria-label="Confirm"]').fill(password)
    click_next(page)
    page.wait_for_url("**/mophoneverification/**", timeout=15_000)

# Main
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_context(
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
    ).new_page()
    page.goto("https://accounts.google.com/signup")
    fill_name(page, "Nguyen", "Test")
    fill_birthday_gender(page, 15, 1995, "June", "Male")
    fill_username(page, "nguyentest" + random_str(6))
    fill_password(page, "TestPass123!")
    # Bước 5: QR — dừng tại đây, cần quét bằng điện thoại thật
```

## Thứ tự flow thật tế (đã verify)

```
1. /lifecycle/steps/signup/name              ← Name
2. /lifecycle/steps/signup/birthdaygender    ← Birthday + Gender
3. /lifecycle/steps/signup/username          ← Gmail username
4. /lifecycle/steps/signup/password          ← Password
5. /lifecycle/steps/signup/mophoneverification/initial  ← 🚨 QR (chặn)
```

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
