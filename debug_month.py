"""Debug month selector."""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_context(locale='en-US', timezone_id='America/New_York').new_page()
    page.goto('https://accounts.google.com/signup')
    page.wait_for_url('**/signup/name**')
    page.locator('#firstName').fill('Nguyen')
    page.locator('#lastName').fill('Test')
    page.locator('button:has-text("Next")').first.click()
    page.wait_for_url('**/birthdaygender**')
    time.sleep(2)

    info = page.evaluate("""() => {
        const out = [];
        // Tìm tất cả element có aria-label chứa Month/Day/Year
        document.querySelectorAll('[aria-label]').forEach(el => {
            const al = el.getAttribute('aria-label') || '';
            if (al.includes('Month') || al.includes('Day') || al.includes('Year')) {
                out.push({
                    tag: el.tagName,
                    role: el.getAttribute('role'),
                    ariaLabel: al,
                    ariaExpanded: el.getAttribute('aria-expanded'),
                    visible: el.offsetParent !== null,
                    jsname: el.getAttribute('jsname') || '',
                    cls: (el.className || '').substring(0, 100),
                    rect: (() => { const r = el.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)} })()
                });
            }
        });
        return out;
    }""")
    for i in info:
        print(i)
    print('---')
    # Tìm button thật để click mở Month — dump tất cả clickable trong vùng
    btns = page.evaluate("""() => {
        // Lấy vùng chứa field "Month"
        const labels = Array.from(document.querySelectorAll('*')).filter(e => {
            return (e.innerText || '').trim() === 'Month' && e.children.length === 0;
        });
        const out = [];
        for (const lbl of labels) {
            const r = lbl.getBoundingClientRect();
            // Tìm element gần label Month (cùng dòng hoặc dưới)
            const candidates = Array.from(document.querySelectorAll('button, [role="combobox"], [role="listbox"], [aria-haspopup]')).filter(c => {
                const cr = c.getBoundingClientRect();
                return Math.abs(cr.y - r.y) < 200 && cr.x > r.x - 50;
            });
            out.push({
                labelText: lbl.innerText,
                labelRect: {x: Math.round(r.x), y: Math.round(r.y)},
                candidates: candidates.map(c => ({
                    tag: c.tagName,
                    role: c.getAttribute('role'),
                    ariaLabel: c.getAttribute('aria-label'),
                    ariaExpanded: c.getAttribute('aria-expanded'),
                    ariaHaspopup: c.getAttribute('aria-haspopup'),
                    dataId: c.getAttribute('data-id'),
                    jsname: c.getAttribute('jsname'),
                    text: (c.innerText || '').substring(0, 60),
                    visible: c.offsetParent !== null,
                    rect: {x: Math.round(c.getBoundingClientRect().x), y: Math.round(c.getBoundingClientRect().y), w: Math.round(c.getBoundingClientRect().width), h: Math.round(c.getBoundingClientRect().height)}
                }))
            });
        }
        return out;
    }""")
    for b2 in btns:
        print(b2)
    b.close()
