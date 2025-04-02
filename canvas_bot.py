from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.environ['SJSU_ID']
PASSWORD = os.environ['SJSU_PASSWORD']

def run_quiz_bot(day: str = '2025-04-04'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Log in and navigate to the calendar
        page.goto('https://sjsu.instructure.com/')
        page.fill('#input28', USERNAME)
        page.fill('#input36', PASSWORD)
        page.click('input.button.button-primary[type="submit"]')
        page.wait_for_timeout(5000)  # Wait for Duo push approval (manual)
        page.wait_for_url("**/sjsu.instructure.com/**", timeout=60000)
        page.click('#global_nav_calendar_link', timeout=10000)
        page.wait_for_timeout(5000)
        page.screenshot(path='screenshots/calendar.png')

        # --- Step 1: Identify the day column using the header cell ---
        day_header_selector = f'td.fc-day-top[data-date="{day}"]'
        day_header = page.query_selector(day_header_selector)
        if not day_header:
            print(f"Day header not found for {day}")
            browser.close()
            return

        day_box = day_header.bounding_box()
        if not day_box:
            print("Could not determine bounding box for the day header.")
            browser.close()
            return

        day_left = day_box['x']
        day_right = day_left + day_box['width']
        print(f"Day cell for {day} is at x: {day_left} with width: {day_box['width']}")

        # --- Step 2: Get all assignment events and filter by horizontal position ---
        page.wait_for_selector('a.fc-day-grid-event.assignment', timeout=10000)
        all_events = page.query_selector_all('a.fc-day-grid-event.assignment')
        matched_events = []

        for event in all_events:
            box = event.bounding_box()
            if not box:
                continue
            # Compute the center x coordinate of the event element.
            event_center_x = box['x'] + box['width'] / 2
            if day_left - 5 <= event_center_x <= day_right + 5:
                matched_events.append(event)

        if not matched_events:
            print(f"No assignments found on {day}")
            browser.close()
            return

        # --- Step 3: Extract a unique identifier (the title) for each matched event ---
        event_titles = []
        for event in matched_events:
            title = event.get_attribute("title")
            if title:
                event_titles.append(title)
        print(f"Found {len(event_titles)} assignment(s) on {day}:")
        for idx, title in enumerate(event_titles):
            print(f"{idx+1}. {title}")

        for idx, title in enumerate(event_titles):
            event_selector = f'a.fc-day-grid-event.assignment[title="{title}"]'
            event = page.query_selector(event_selector)
            if event:
                print(f"Opening assignment preview {idx+1}: {title}")
                event.click()  # First click opens preview
                page.wait_for_timeout(1000)

                # Wait for the preview popup to appear
                page.wait_for_selector('#popover-0', timeout=5000)

                # Find the link inside the preview that fully opens the assignment
                # Usually an <a> inside the preview
                full_view_link = page.query_selector('#popover-0 a')
                if full_view_link:
                    print("➡ Clicking full view link in preview")
                    full_view_link.click()
                    page.wait_for_timeout(3000)
                    page.screenshot(path=f'screenshots/assignment_{idx+1}.png')
                    page.go_back()
                    page.wait_for_timeout(2000)
                else:
                    print("⚠️ Could not find full-view link inside preview popup.")
                    page.keyboard.press("Escape")  # Close popup as fallback
                    page.wait_for_timeout(1000)
            else:
                print(f"❌ Could not find event: {title}")
            browser.close()

# Run the bot for a specific day (ISO format: YYYY-MM-DD)
run_quiz_bot('2025-04-04')