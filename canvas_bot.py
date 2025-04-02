from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import main 

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
        
        # --- Step 1: Get all assignment events for the target day ---
        # We'll assume events are filtered by horizontal position using the day header.
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

        page.wait_for_selector('a.fc-day-grid-event.assignment', timeout=10000)
        all_events = page.query_selector_all('a.fc-day-grid-event.assignment')
        matched_events = []

        for event in all_events:
            box = event.bounding_box()
            if not box:
                continue
            event_center_x = box['x'] + box['width'] / 2
            if day_left - 5 <= event_center_x <= day_right + 5:
                matched_events.append(event)

        if not matched_events:
            print(f"No assignments found on {day}")
            browser.close()
            return

        # Extract unique titles from matched events
        event_titles = []
        for event in matched_events:
            title = event.get_attribute("title")
            if title:
                event_titles.append(title)
        print(f"Found {len(event_titles)} assignment(s) on {day}:")
        for idx, title in enumerate(event_titles):
            print(f"{idx+1}. {title}")

        # --- Step 2: Iterate over each event and extract its instructions ---
        for idx, title in enumerate(event_titles):
            event_selector = f'a.fc-day-grid-event.assignment[title="{title}"]'
            event = page.query_selector(event_selector)
            if event:
                print(f"Opening assignment preview for: {title}")
                event.click()  # Click to open preview popup
                page.wait_for_timeout(1000)  # Wait for preview to load

                # Wait for the preview popup and then click the "view event" link
                page.wait_for_selector('div.event-details a.view_event_link', timeout=5000)
                view_link = page.query_selector('div.event-details a.view_event_link')
                if view_link:
                    print("Clicking the 'view event' link to open full assignment.")
                    view_link.click()  # Redirects to the full assignment page
                    page.wait_for_timeout(3000)
                else:
                    print("Could not find the full-view link. Pressing Escape as fallback.")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)
                    continue

                # --- Step 3: Extract assignment instructions from the full page ---
                # The instructions are in a div with classes "description user_content enhanced"
                page.wait_for_selector('div.description.user_content.enhanced', timeout=5000)
                instructions_element = page.query_selector('div.description.user_content.enhanced')
                if instructions_element:
                    instructions = instructions_element.inner_text()
                    print(f"\n📝 Assignment {idx+1} Instructions:\n{instructions}\n")
                    
                    # Optionally, send `instructions` to your LangChain agent here.
                    # For example:
                    # from langchain.chat_models import ChatOpenAI
                    # from langchain.schema import HumanMessage
                    # llm = ChatOpenAI(model_name="gpt-4", temperature=0)
                    # response = llm([HumanMessage(content=instructions)])
                    # print("🤖 Agent Response:\n", response.content)
                    main.agent_task(instructions)
                else:
                    print("Could not locate assignment instructions.")

                page.screenshot(path=f'screenshots/assignment_{idx+1}.png')
                page.go_back()  # Return to calendar
                page.wait_for_timeout(2000)
            else:
                print(f"Could not find event with title: {title}")

        browser.close()

# Run the bot for a specific day (ISO format: YYYY-MM-DD)
run_quiz_bot('2025-04-04')