"""
Gmail Signup AUTO — chạy đến QR rồi dừng.
Selectors dựa trên bản ghi gmail.json thật của bạn (locale vi, viewport 615x729).

Key findings (từ gmail.json):
- Locale: vi (Vietnamese)
- Viewport: 615 × 729
- Month:  click  #month > div > div[1] > div          (button mở dropdown)
           click  #month li:nth-of-type(5)            (option tháng 5)
- Gender: click  #gender > div > div[1] > div
           click  #gender li:nth-of-type(1)           (option Nữ = index 1)
- Day:    input #day
- Year:   input #year
- Username: aria/Tên người dùng → input
- Password: #passwd ... input  (nth-of-type 1)
- Confirm:  #confirm-passwd ... input (nth-of-type 2)
- Next button IDs:
    name            → #collectNameNext
    birthdaygender  → #birthdaygenderNext
    username        → #next
    password        → #createpasswordNext
"""
import os
import sys
import random
import string
import time

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout


def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def click_btn_by_id(page: Page, btn_id: str):
    """Click Next — dùng id riêng của từng step."""
    page.locator(f'#{btn_id}').wait_for(state="visible", timeout=10_000)
    page.locator(f'#{btn_id}').click()


def click_dropdown_option(page: Page, dropdown_id: str, option_index: int):
    """
    Click button mở dropdown → click option theo index (1-based).
    dropdown_id: 'month' or 'gender'
    option_index:
        month  → 1..12 (1=January, 5=May, ...)
        gender → 1=Nữ, 2=Nam, 3=Không muốn nói, 4=Khác
    """
    opener = page.locator(f'#{dropdown_id} > div > div:nth-of-type(1) > div').first
    opener.wait_for(state="visible", timeout=10_000)
    opener.click()
    # Listbox options
    opt = page.locator(f'#{dropdown_id} li:nth-of-type({option_index})').first
    opt.wait_for(state="visible", timeout=5_000)
    opt.click()
    time.sleep(0.4)


def fill_name(page: Page, first: str, last: str):
    print(f"  [1/5] Name: {last} {first}")
    page.locator('#firstName').wait_for(state="visible", timeout=10_000)
    page.locator('#lastName').fill(last)
    page.locator('#firstName').fill(first)
    click_btn_by_id(page, 'collectNameNext')
    page.wait_for_url("**/birthdaygender**", timeout=15_000)


def fill_birthday_gender(page: Page, day: int, year: int, month_index: int = 5, gender_index: int = 2):
    """
    month_index: 1..12 (5 = Tháng 5 / May)
    gender_index: 1=Nữ, 2=Nam, 3=Không muốn nói, 4=Khác
    """
    print(f"  [2/5] Birthday: day={day} month#{month_index} year={year} gender#{gender_index}")
    page.locator('#day').wait_for(state="visible", timeout=10_000)

    # Day (input type=tel)
    page.locator('#day').fill(str(day))

    # Month
    click_dropdown_option(page, 'month', month_index)

    # Year
    page.locator('#year').fill(str(year))

    # Gender
    click_dropdown_option(page, 'gender', gender_index)

    click_btn_by_id(page, 'birthdaygenderNext')
    page.wait_for_url("**/username**", timeout=15_000)


def fill_username(page: Page, username: str):
    print(f"  [3/5] Username: {username}")
    page.wait_for_url("**/username**", timeout=15_000)
    # Selector dựa trên gmail.json: aria-label="Tên người dùng" + tag input
    inp = page.locator('input[aria-label="Tên người dùng"]').first
    inp.wait_for(state="visible", timeout=10_000)
    inp.fill(username)
    click_btn_by_id(page, 'next')
    page.wait_for_url("**/password**", timeout=15_000)


def fill_password(page: Page, password: str):
    print(f"  [4/5] Password: {password[:3]}***")
    page.wait_for_url("**/password**", timeout=15_000)

    pwd = page.locator('#passwd input').first
    pwd.wait_for(state="visible", timeout=10_000)
    pwd.fill(password)

    cfm = page.locator('#confirm-passwd input').first
    cfm.fill(password)

    click_btn_by_id(page, 'createpasswordNext')
    page.wait_for_url("**/mophoneverification/**", timeout=20_000)


def main():
    print("=" * 60)
    print("GMAIL SIGNUP AUTO — selectors from gmail.json (vi locale)")
    print("=" * 60)

    username = f"nguyentest{rand_str(8)}"
    password = "TestPass123!"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={"width": 615, "height": 729},
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",  # match locale vi-VN
            color_scheme="light",
        )
        page = context.new_page()

        print("\n[0/5] Mở signup...")
        page.goto("https://accounts.google.com/signup", timeout=30_000, wait_until="domcontentloaded")
        page.wait_for_url("**/signup/name**", timeout=15_000)
        print(f"  → URL: {page.url[:90]}...")

        fill_name(page, "Ngoc", "Minh")
        print(f"  ✓ {page.url[:60]}...")

        fill_birthday_gender(page, day=12, year=2005, month_index=5, gender_index=1)
        print(f"  ✓ {page.url[:60]}...")

        fill_username(page, username)
        print(f"  ✓ {page.url[:60]}...")

        fill_password(page, password)
        print(f"  ✓ {page.url[:60]}...")

        print("\n[5/5] Doi QR...")
        time.sleep(2)
        qr_selectors = [
            'img[alt*="QR code"]',
            'img[alt*="QR"]',
            'img[src*="data:image/png"]',
        ]
        qr_found = None
        for sel in qr_selectors:
            loc = page.locator(sel)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    qr_found = (sel, loc.nth(i))
                    break
            if qr_found:
                break

        if qr_found:
            sel, qr = qr_found
            print(f"  [OK] QR found via: {sel}")
            print(f"  -> URL: {page.url[:90]}")
            print(f"  -> Username: {username}@gmail.com")
            print(f"  -> Password: {password}")
            ss = r"c:\Users\Admin\Documents\Gmail\investigation\qr_auto.png"
            qr.screenshot(path=ss)
            print(f"  -> Screenshot: {ss}")
            print("\nBrowser mo - quet QR tren dien thoai.")
            try:
                page.wait_for_url(lambda u: "mophoneverification" not in u, timeout=300_000)
                print(f"\nDa quet! Next: {page.url[:80]}")
            except PWTimeout:
                print("\nTimeout.")
        else:
            print("  [ERR] QR khong tim thay")
            print(f"  -> URL: {page.url}")
            ss = r"c:\Users\Admin\Documents\Gmail\investigation\qr_debug.png"
            page.screenshot(path=ss, full_page=True)
            print(f"  -> Debug: {ss}")

        print("\nDong browser sau 5 giay...")
        time.sleep(5)
        browser.close()


if __name__ == "__main__":
    main()
