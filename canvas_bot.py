import nest_asyncio
nest_asyncio.apply()  # Patch the event loop so we can run nested loops

import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import pdfplumber
import main  # Assuming your agent_task function lives here
import checking_bot as nerd 

load_dotenv()

USERNAME = os.environ['SJSU_ID']
PASSWORD = os.environ['SJSU_PASSWORD']



def download_pdf_from_assignment(page):
    # Use a robust attribute-based selector to target the download link.
    download_link_selector = "a[href*='download?download_frd=1']"
    # Wait for the element to be attached (present in the DOM) regardless of visibility.
    download_link_element = page.wait_for_selector(download_link_selector, state="attached", timeout=5000)
    
    if not download_link_element:
        print('Download link not found')
        return None

    # Use evaluate to click the element via JavaScript, which bypasses visibility checks.
    with page.expect_download() as download_info:
        page.evaluate("element => element.click()", download_link_element)
    download = download_info.value
    pdf_filename = download.suggested_filename or "downloaded_assignment.pdf"
    os.makedirs('downloads', exist_ok=True)
    download_path = os.path.join("downloads", pdf_filename)
    download.save_as(download_path)
    print(f"PDF downloaded: {pdf_filename}")
    return download_path

#this is where we store the answers to the assignments, before second agent reviews it

def create_txt_file(txt: str):
    os.makedirs('answers', exist_ok=True)
    file_path = os.path.join('answers', 'answers.txt')
    with open(file_path, 'w') as file:
        file.write(txt)
    print(f"Answers saved to {file_path}")

    
    
    


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                page_text = p.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def screenshot_pdf_view(browser, pdf_url: str, screenshot_path: str):
    # Open the PDF URL in a new page to capture a screenshot.
    pdf_page = browser.new_page()
    try:
        pdf_page.goto(pdf_url, timeout=15000)
        pdf_page.wait_for_timeout(2000)  # Wait for the PDF to render
        pdf_page.screenshot(path=screenshot_path, full_page=True)
        print(f"PDF screenshot saved as {screenshot_path}")
    except Exception as e:
        print(f"Error taking PDF screenshot: {e}")
    finally:
        pdf_page.close()

        
def check_work(instructions : str, answers, pdf=None):
    grade = nerd.check_work(instructions, answers, pdf)
    if grade['passed']:
        return True
    else:
        return grade['feedback']


def login_and_open_calendar(page):
    page.goto('https://sjsu.instructure.com/')
    page.fill('#input28', USERNAME)
    page.fill('#input36', PASSWORD)
    page.click('input.button.button-primary[type="submit"]')
    page.wait_for_timeout(5000)
    page.wait_for_url("**/sjsu.instructure.com/**", timeout=60000)
    page.click('#global_nav_calendar_link', timeout=10000)
    page.wait_for_timeout(5000)
    page.screenshot(path='screenshots/calendar.png')

def get_day_events(page, day):
    day_header_selector = f'td.fc-day-top[data-date="{day}"]'
    day_header = page.query_selector(day_header_selector)
    if not day_header:
        print(f"Day header not found for {day}")
        return []
    day_box = day_header.bounding_box()
    if not day_box:
        print("Could not determine bounding box for the day header.")
        return []
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
    return matched_events

def get_event_titles(events):
    titles = []
    for event in events:
        title = event.get_attribute("title")
        if title:
            titles.append(title)
    return titles

def process_assignment(page, browser, idx, title):
    event_selector = f'a.fc-day-grid-event.assignment[title="{title}"]'
    event = page.query_selector(event_selector)
    if not event:
        print(f"❌ Could not find event with title: {title}")
        return

    print(f"Opening assignment preview for: {title}")
    event.click()
    page.wait_for_timeout(1000)
    page.wait_for_selector('div.event-details a.view_event_link', timeout=5000)
    view_link = page.query_selector('div.event-details a.view_event_link')
    if view_link:
        print("Clicking the 'view event' link to open full assignment.")
        view_link.click()
        page.wait_for_timeout(3000)
    else:
        print("Full-view link not found; pressing Escape as fallback.")
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)
        return

    page.wait_for_selector('div.description.user_content.enhanced', timeout=5000)
    instructions_element = page.query_selector('div.description.user_content.enhanced')
    if not instructions_element:
        print("Could not locate assignment instructions.")
        return

    instructions = instructions_element.inner_text()
    print(f"\n📝 Assignment {idx+1} Instructions:\n{instructions}\n")
    download_link = instructions_element.query_selector("a[href*='download?download_frd=1']")
    if download_link:
        print("📎 Found attached PDF. Attempting download...")
        pdf_filename = download_pdf_from_assignment(page)
        if pdf_filename:
            os.makedirs('downloads', exist_ok=True)
            pdf_url = download_link.get_attribute("href")
            if pdf_url:
                screenshot_pdf_view(browser, pdf_url, os.path.join("downloads", f"screenshot_{pdf_filename}.png"))
            pdf_text = extract_text_from_pdf(pdf_path=pdf_filename)
            print("📄 Extracted PDF Content (first 500 characters):\n", pdf_text[:500], "...\n")
            full_prompt = instructions + "\n\nAlso consider this attached PDF:\n" + pdf_text
        else:
            full_prompt = instructions
    else:
        print("⚠️ No downloadable PDF link found. Using only instructions.")
        full_prompt = instructions
    answers = main.agent_task(full_prompt)
    valid = check_work(instructions_element, answers, pdf_text)
    if valid:
        create_txt_file(answers)
    


def download_pdf_from_assignment(page):
    download_link_selector = "a[href*='download?download_frd=1']"
    download_link_element = page.wait_for_selector(download_link_selector, state="attached", timeout=5000)
    if not download_link_element:
        print('Download link not found')
        return None
    with page.expect_download() as download_info:
        page.evaluate("element => element.click()", download_link_element)
    download = download_info.value
    pdf_filename = download.suggested_filename or "downloaded_assignment.pdf"
    os.makedirs('downloads', exist_ok=True)
    download_path = os.path.join("downloads", pdf_filename)
    download.save_as(download_path)
    print(f"PDF downloaded: {pdf_filename}")
    return download_path

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                page_text = p.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def screenshot_pdf_view(browser, pdf_url: str, screenshot_path: str):
    pdf_page = browser.new_page()
    try:
        pdf_page.goto(pdf_url, timeout=15000)
        pdf_page.wait_for_timeout(2000)
        pdf_page.screenshot(path=screenshot_path, full_page=True)
        print(f"PDF screenshot saved as {screenshot_path}")
    except Exception as e:
        print(f"Error taking PDF screenshot: {e}")
    finally:
        pdf_page.close()

def create_txt_file(txt: str):
    os.makedirs('answers', exist_ok=True)
    file_path = os.path.join('answers', 'answers.txt')
    with open(file_path, 'w') as file:
        file.write(txt)

def run_assignment_flow(day: str = '2025-04-04'):
    p = sync_playwright().start()
    try:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_and_open_calendar(page)
        matched_events = get_day_events(page, day)
        if not matched_events:
            print(f"No assignments found on {day}")
            return
        titles = get_event_titles(matched_events)
        print(f"Found {len(titles)} assignment(s) on {day}:")
        for idx, title in enumerate(titles):
            print(f"{idx+1}. {title}")
        for idx, title in enumerate(titles):
            process_assignment(page, browser, idx, title)
    except Exception as e:
        print("Error during run_assignment_flow:", e)
    finally:
        try:
            browser.close()
        except Exception as ex:
            print("Error closing browser:", ex)
        p.stop()

# Run the flow for a given day
if __name__ == "__main__":
    run_assignment_flow('2025-04-04')


