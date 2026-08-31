"""
Gmail Signup INTERACTIVE Investigator
Mở Chrome thật, dump cấu trúc trang, bạn tự điền tay qua browser.
Mỗi lần page thay đổi sẽ dump inputs/buttons/text để quan sát.
Khi thấy QR sẽ dump full context.
"""
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Force UTF-8 for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from playwright.sync_api import sync_playwright

WORKSPACE = Path(r"c:\Users\Admin\Documents\Gmail\investigation")
LOG_FILE = WORKSPACE / "interactive_log.txt"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    """Print + write to file."""
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def dump_inputs(page):
    """List all interactive inputs."""
    try:
        return page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
                return inputs.map(el => ({
                    tag: el.tagName,
                    type: el.type,
                    name: el.name || '',
                    id: el.id || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    placeholder: el.placeholder || '',
                    value: el.value || '',
                    visible: el.offsetParent !== null,
                    rect: (() => { const r = el.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)} })()
                }));
            }
        """)
    except Exception as e:
        return [{"error": str(e)}]

def dump_buttons(page):
    try:
        return page.evaluate("""
            () => {
                const btns = Array.from(document.querySelectorAll('button, [role="button"], a[href]'));
                return btns.map(el => ({
                    tag: el.tagName,
                    text: (el.innerText || '').trim().substring(0, 60),
                    ariaLabel: el.getAttribute('aria-label') || '',
                    visible: el.offsetParent !== null,
                    disabled: el.disabled || false,
                    href: el.href || ''
                })).filter(b => b.visible && (b.text || b.ariaLabel));
            }
        """)
    except Exception as e:
        return [{"error": str(e)}]

def dump_texts(page, max_len=300):
    try:
        return page.evaluate("""
            () => {
                const items = [];
                const els = document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,label,span,div[role="heading"],div[role="alert"],strong,b');
                for (const el of els) {
                    const t = el.innerText.trim();
                    if (t.length > 2 && t.length < 800) items.push(t);
                }
                return [...new Set(items)].slice(0, 80);
            }
        """)
    except:
        return []

def dump_qr_context(page):
    """Detailed QR analysis."""
    return page.evaluate("""
        () => {
            const result = { qrFound: false, details: {} };

            // 1. Find QR image
            const imgs = Array.from(document.querySelectorAll('img'));
            const qrImg = imgs.find(i => {
                const alt = (i.alt||'').toLowerCase();
                const src = (i.src||'').toLowerCase();
                return alt.includes('qr') || src.includes('qr') ||
                       src.includes('tactile') || src.includes('barcode') ||
                       src.includes('otpauth') || src.includes('chart.googleapis');
            });

            // 2. Find QR canvas (square non-chart)
            const canvases = Array.from(document.querySelectorAll('canvas'));
            const qrCanvas = canvases.find(c => {
                if (c.width < 80) return false;
                return Math.abs(c.width - c.height) < 30;
            });

            // 3. Find any element with QR background
            const qrBg = Array.from(document.querySelectorAll('div,section')).find(d => {
                const s = (d.getAttribute('style')||'').toLowerCase();
                return s.includes('qr') || s.includes('tactile') || s.includes('barcode');
            });

            // 4. Find text mentioning scan/QR
            const scanText = Array.from(document.querySelectorAll('*')).find(e => {
                const t = (e.innerText||'').toLowerCase();
                return t.includes('scan with your phone') ||
                       t.includes('scan this code') ||
                       t.includes('use your phone to sign in') ||
                       t.includes('quét mã');
            });

            if (qrImg) {
                result.qrFound = true;
                result.details.type = 'img';
                result.details.src = qrImg.src.substring(0, 500);
                result.details.alt = qrImg.alt;
                result.details.width = qrImg.width;
                result.details.height = qrImg.height;

                // Get parent context
                let parent = qrImg.parentElement;
                let depth = 0;
                while (parent && depth < 4) {
                    const txt = (parent.innerText || '').substring(0, 500);
                    if (txt.includes('Scan') || txt.includes('phone') || txt.includes('sign in') || txt.length > 50) break;
                    parent = parent.parentElement;
                    depth++;
                }
                if (parent) {
                    result.details.parentTag = parent.tagName;
                    result.details.parentClass = (parent.className || '').substring(0, 200);
                    result.details.parentText = (parent.innerText || '').substring(0, 1000);
                }
            } else if (qrCanvas) {
                result.qrFound = true;
                result.details.type = 'canvas';
                result.details.width = qrCanvas.width;
                result.details.height = qrCanvas.height;
            } else if (qrBg) {
                result.qrFound = true;
                result.details.type = 'bg_div';
                result.details.html = qrBg.outerHTML.substring(0, 500);
                result.details.text = (qrBg.innerText || '').substring(0, 500);
            } else if (scanText) {
                result.qrFound = true;
                result.details.type = 'text_only';
                result.details.text = (scanText.innerText || '').substring(0, 1000);
            }

            return result;
        }
    """)

def dump_state(page, step_num, label):
    """One-shot dump."""
    info = {
        "url": page.url,
        "title": page.title(),
        "inputs": dump_inputs(page),
        "buttons": dump_buttons(page),
        "texts": dump_texts(page),
        "qr": dump_qr_context(page),
    }
    return info

def print_state(info, step_num, label):
    log(f"\n{'='*70}")
    log(f"STEP {step_num}: {label}")
    log(f"{'='*70}")
    log(f"URL: {info['url']}")
    log(f"Title: {info['title']}")
    log(f"\n📋 TEXT ON PAGE ({len(info['texts'])} items):")
    for t in info['texts']:
        log(f"   {t}")
    log(f"\n⌨️  INPUTS ({len(info['inputs'])} items):")
    for i in info['inputs']:
        if i.get('visible') or i.get('type') == 'hidden':
            log(f"   {json.dumps(i, ensure_ascii=False)}")
    log(f"\n🔘 BUTTONS ({len(info['buttons'])} items):")
    for b in info['buttons']:
        log(f"   {json.dumps(b, ensure_ascii=False)}")
    if info['qr'].get('qrFound'):
        log(f"\n🚨 QR CODE DETECTED:")
        log(f"   {json.dumps(info['qr']['details'], indent=2, ensure_ascii=False)}")
    log("")

# ─── Main flow ────────────────────────────────────────────────────────────────
log(f"\n{'#'*70}")
log(f"# GMAIL INTERACTIVE INVESTIGATOR — STARTED {datetime.now().isoformat()}")
log(f"# Open browser window → fill form by hand → script logs state per step")
log(f"{'#'*70}\n")

last_url = None
step_counter = 0

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-first-run',
            '--disable-extensions',
        ]
    )
    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
        color_scheme="light",
    )

    # Track console errors
    console_errors = []
    def on_console(msg):
        if msg.type == "error":
            err = msg.text[:200]
            console_errors.append(err)
            log(f"   [CONSOLE ERROR] {err}")
    context.on("console", lambda msg: on_console(msg) if msg.type == "error" else None)

    # Track failed network requests to Google
    def on_response(resp):
        if 'accounts.google' in resp.url and resp.status >= 400:
            log(f"   [HTTP {resp.status}] {resp.url[:120]}")
    context.on("response", on_response)

    page = context.new_page()

    # Goto signup
    log("🚀 Opening https://accounts.google.com/signup ...")
    page.goto("https://accounts.google.com/signup", timeout=30000, wait_until="domcontentloaded")
    time.sleep(2)

    step_counter += 1
    info = dump_state(page, step_counter, "Initial signup page")
    print_state(info, step_counter, "Initial signup page")
    last_url = info['url']

    # Watch for URL changes → dump state on each
    log("\n👀 Watching for page changes for up to 120s (Ctrl+C to stop earlier)...")
    log("   → Điền form bằng tay trên browser, script sẽ tự dump mỗi khi trang thay đổi")
    log("   → Nhấn ENTER ở terminal này để dump lại state hiện tại\n")

    start = time.time()
    try:
        while time.time() - start < 120:
            try:
                page.wait_for_url(lambda url: url != last_url, timeout=2000)
            except:
                pass

            current_url = page.url
            if current_url != last_url:
                step_counter += 1
                time.sleep(1.5)
                info = dump_state(page, step_counter, f"URL changed → {current_url[-60:]}")
                print_state(info, step_counter, f"URL changed → {current_url[-60:]}")
                last_url = current_url

                # Check QR
                if info['qr'].get('qrFound'):
                    log("🚨🚨🚨 QR DETECTED — STOPPING 🚨🚨🚨")
                    log(f"Full QR context saved. URL: {current_url}")
                    break
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        log("\n⏹️  Stopped by user")

    browser.close()

log(f"\n✅ Done. Log saved to: {LOG_FILE}")
log(f"   Total steps logged: {step_counter}")
log(f"   Console errors captured: {len(console_errors)}")
