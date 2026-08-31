"""Replace QR block in gmail_auto.py."""
import re

with open('gmail_auto.py', 'r', encoding='utf-8') as f:
    s = f.read()

# Find marker for QR section
m = re.search(r'        # Step 5 .{1,3} QR\n', s)
if not m:
    print('Marker not found')
    raise SystemExit(1)
start = m.start()

# Find end: last "browser.close()" before the if __name__
end_marker = "if __name__"
end_idx = s.find(end_marker, start)
if end_idx < 0:
    print('end not found')
    raise SystemExit(1)

# Find last "browser.close()" before that
close_idx = s.rfind('        browser.close()', start, end_idx)
if close_idx < 0:
    print('browser.close not found')
    raise SystemExit(1)
end = close_idx + len('        browser.close()')

print('Replacing bytes', start, 'to', end)
print('Old preview:', s[start:start+80])

new_block = '''        print("\\n[5/5] Doi QR...")
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
            ss = r"c:\\Users\\Admin\\Documents\\Gmail\\investigation\\qr_auto.png"
            qr.screenshot(path=ss)
            print(f"  -> Screenshot: {ss}")
            print("\\nBrowser mo - quet QR tren dien thoai.")
            try:
                page.wait_for_url(lambda u: "mophoneverification" not in u, timeout=300_000)
                print(f"\\nDa quet! Next: {page.url[:80]}")
            except PWTimeout:
                print("\\nTimeout.")
        else:
            print("  [ERR] QR khong tim thay")
            print(f"  -> URL: {page.url}")
            ss = r"c:\\Users\\Admin\\Documents\\Gmail\\investigation\\qr_debug.png"
            page.screenshot(path=ss, full_page=True)
            print(f"  -> Debug: {ss}")

        print("\\nDong browser sau 5 giay...")
        time.sleep(5)
        browser.close()'''

new_s = s[:start] + new_block + s[end:]
with open('gmail_auto.py', 'w', encoding='utf-8') as f:
    f.write(new_s)
print('OK, new file written')
