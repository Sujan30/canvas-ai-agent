from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def check_scribbr(sample_text: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("➡️  Navigating to Scribbr AI Detector…")
        page.goto("https://www.scribbr.com/ai-detector/", timeout=60000, wait_until="domcontentloaded")

        # 1️⃣  Wait for the contenteditable to be present in the DOM
        editor_selector = 'div[data-testid="aidr-input-editor"]'
        page.wait_for_selector(editor_selector, state="attached", timeout=20000)

        # 2️⃣  Click it to focus
        print("✏️  Focusing the editor…")
        page.click(editor_selector)

        # 3️⃣  Clear any placeholder (Cmd+A / Backspace)
        page.keyboard.press("Meta+A")    # on Mac: Cmd+A
        page.keyboard.press("Backspace")

        # 4️⃣  “Paste” your text via keyboard
        print("📋  Inserting text…")
        page.keyboard.insert_text(sample_text)

        # 5️⃣  Trigger detection
        print("🔍  Clicking Detect AI…")
        page.click('button[data-testid="aidr-primary-cta"]')

        # 6️⃣  Wait for the results box
        try:
            page.wait_for_selector('[data-testid="aidr-output-box"]', state="visible", timeout=60000)
            print("✅  Results are visible!")
        except PlaywrightTimeoutError:
            print("❌  Timed out waiting for results.")

        browser.close()


if __name__ == "__main__":
    long_text = f"This fixes the Event loop is closed! error because now we're properly handling the Playwright context. The browser is closed within the same context it was created in, and we have proper error handling for all operations. Try running the script again - the event loop issue should be resolved. If you're still having issues with the editor not being found, we may need to try different selectors or approaches to interact with the Scribbr site. This approach skips the problematic paste-upload container completely and tries to interact directly with the editor. Run this script and check the screenshots folder to see what's being displayed at each step. This should help identify exactly what's happening on the page. This approach skips the problematic paste-upload container completely and tries to interact directly with the editor. Run this script and check the screenshots folder to see what's being displayed at each step. This should help identify exactly what's happening on the page."  # ≥80 words here
    check_scribbr(long_text)