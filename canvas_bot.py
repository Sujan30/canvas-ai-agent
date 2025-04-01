from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import difflib
import datetime as date

load_dotenv()

USERNAME = os.environ['SJSU_ID']
PASSWORD = os.environ['SJSU_PASSWORD']

def match_answer_to_option(answer, options):
    return difflib.get_close_matches(answer, options, n=1, cutoff=0.4)[0]

def run_quiz_bot(day: str = date.date.today().isoformat()):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto('https://sjsu.instructure.com/')
    page.fill('#input28', USERNAME)
    page.fill('#input36', PASSWORD)  
    page.click('input.button.button-primary[type="submit"]')
    
    page.wait_for_timeout(5000)  # wait for Duo push notification prompt
    # Human approves Duo push notification here...
    page.wait_for_url("**/sjsu.instructure.com/**", timeout=60000)
    page.screenshot(path='screenshots/dashboard.png')
    
    page.click('#global_nav_calendar_link', timeout=10000)
    page.wait_for_timeout(10000)
    page.screenshot(path='screenshots/calendar.png')
    
    # Wait until at least one event is visible.
    page.wait_for_selector('a.fc-day-grid-event', timeout=10000)
    all_events = page.query_selector_all('a.fc-day-grid-event')
    
    matched_events = []
    # For each event, traverse the ancestors to find a node with a data-date attribute.
    for event in all_events:
        parent_date = event.evaluate(
            """el => {
                   let current = el;
                   while (current) {
                       if (current.hasAttribute && current.hasAttribute("data-date")) {
                           return current.getAttribute("data-date");
                       }
                       current = current.parentElement;
                   }
                   return null;
               }"""
        )
        if parent_date == day:
            matched_events.append(event)
    
    if matched_events:
        print(f"Clicking the first assignment for {day}")
        matched_events[0].click()
        page.screenshot(path='screenshots/assignment.png')
    else:
        print(f"No assignments found for {day}")
    
    browser.close()
    p.stop()

# Example usage: run for a specific day (ISO format: YYYY-MM-DD)
run_quiz_bot(day='2025-04-04')