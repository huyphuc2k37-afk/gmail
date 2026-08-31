"""Debug username selector."""
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

    # Fill birthday
    page.locator('div[role="combobox"][jsname="oYxtQd"]').filter(has_text="Month").first.click()
    page.locator('li[role="option"]:has-text("June")').first.click()
    time.sleep(0.5)
    page.locator('input[name="day"]').fill('15')
    page.locator('input[name="year"]').fill('1995')
    page.locator('div[role="combobox"][jsname="oYxtQd"]').filter(has_text="Gender").first.click()
    page.locator('li[role="option"]:has-text("Male")').first.click()
    time.sleep(0.5)
    page.locator('button:has-text("Next")').first.click()
    page.wait_for_url('**/username**')
    time.sleep(1)

    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input')).map(el => ({
            tag: el.tagName,
            type: el.type,
            name: el.name || '',
            id: el.id || '',
            ariaLabel: el.getAttribute('aria-label') || '',
            placeholder: el.placeholder || '',
            visible: el.offsetParent !== null,
            rect: (() => { const r = el.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)} })()
        }));
    }""")
    for i in inputs:
        print(i)
    b.close()
