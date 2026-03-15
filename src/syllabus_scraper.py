import time
import re
import json
from datetime import datetime
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless=True):
    """Setup Chrome driver with options to bypass bot detection"""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def convert_course_number(course_num):
    """Convert course number format from 89-680 to 89680"""
    return course_num.replace("-", "")


def wait_for_search_form(driver, timeout=60):
    """
    Wait for the BIU search form to become available.
    The site can briefly show a Radware verification page before the real form.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            code_input = driver.find_element(By.ID, 'ContentPlaceHolder1_txLessonCode')
            if code_input.is_displayed():
                return code_input
        except Exception:
            pass
        time.sleep(1)

    raise TimeoutError("Search form did not load in time")

def extract_weekly_topics(syllabus_text):
    """
    Heuristically extract weekly topics from the syllabus text.
    Looks for patterns like 'שבוע 1', 'מפגש 1', 'Week 1' or lists of topics.
    """
    topics = []
    
    # Try to find a section that looks like a schedule
    schedule_patterns = [
        r'(?:תכנית|נושאי) ה(?:לימודים|קורס)(.+?)(?=\n\n|\Z)',
        r'(?:Schedule|Topics)(.+?)(?=\n\n|\Z)',
        r'(?:סילבוס|Syllabus)(.+?)(?=\n\n|\Z)'
    ]
    
    schedule_text = syllabus_text
    for pattern in schedule_patterns:
        match = re.search(pattern, syllabus_text, re.DOTALL | re.IGNORECASE)
        if match:
            schedule_text = match.group(1)
            break

    # Look for numbered weeks or lines
    lines = schedule_text.split('\n')
    current_topic = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Match 'Week X', 'שבוע X', '1.', etc.
        week_match = re.match(r'^(?:שבוע|מפגש|Week|Lesson)\s*(\d+)[:.-]?\s*(.*)', line, re.IGNORECASE)
        if week_match:
            week_num = week_match.group(1)
            topic_desc = week_match.group(2).strip()
            topics.append({"week": week_num, "topic": topic_desc})
        elif re.match(r'^\d+[\s.)-]', line):
            # Just a numbered list
            parts = re.split(r'[\s.)-]', line, 1)
            if len(parts) > 1:
                topics.append({"week": parts[0], "topic": parts[1].strip()})
    
    return topics

def get_course_syllabus(course_num, headless=True):
    """
    Search for a course and extract its syllabus content and topics.
    """
    driver = setup_driver(headless=headless)
    clean_num = convert_course_number(course_num)
    
    result = {
        "course_num": course_num,
        "found": False,
        "syllabus_text": "",
        "topics": [],
        "course_name": "",
        "lecturer": "",
        "semester": "",
        "course_type": "",
        "department": "",
        "search_term": "המחלקה למדעי המחשב",
        "source_url": "",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "errors": []
    }
    
    try:
        driver.get('https://courses.biu.ac.il/')
        
        # Search for course
        code_input = wait_for_search_form(driver, timeout=60)
        code_input.clear()
        code_input.send_keys(clean_num)
        
        search_btn = driver.find_element(By.ID, 'ContentPlaceHolder1_btnSearch')
        search_btn.click()
        
        # Find first result (preferring 'הרצאה')
        time.sleep(2)
        rows = driver.find_elements(By.CSS_SELECTOR, "tr")
        lecture_link = None
        lecture_row_text = ""
        lecture_href = ""
        
        for row in rows:
            if clean_num in row.text and ('הרצאה' in row.text or 'Lecture' in row.text):
                links = row.find_elements(By.TAG_NAME, 'a')
                if links:
                    lecture_link = links[0]
                    lecture_row_text = row.text
                    lecture_href = lecture_link.get_attribute("href") or ""
                    break
        
        if not lecture_link:
            # Fallback to any link with course code
            links = driver.find_elements(By.CSS_SELECTOR, f"a[href*='CourseDetails']")
            if links:
                lecture_link = links[0]
                lecture_href = lecture_link.get_attribute("href") or ""
        
        if lecture_link:
            if lecture_row_text:
                row_lines = [x.strip() for x in lecture_row_text.splitlines() if x.strip()]
                if len(row_lines) >= 2:
                    # Expected pattern: [code, name, group, lecturer, type, ...]
                    result["course_name"] = row_lines[1]
                if len(row_lines) >= 4:
                    result["lecturer"] = row_lines[3]
                if len(row_lines) >= 5:
                    result["course_type"] = row_lines[4]
                semester_line = next((x for x in row_lines if "סמסטר" in x), "")
                if semester_line:
                    result["semester"] = semester_line

            if lecture_href:
                driver.get(lecture_href)
            else:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lecture_link)
                    lecture_link.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", lecture_link)

            result["source_url"] = driver.current_url

            # Parse details page text for stable metadata even if table order changes.
            details_text = driver.find_element(By.TAG_NAME, 'body').text

            if not result["course_name"]:
                title_match = re.search(rf"{re.escape(clean_num)}\s+([^\n]+)", details_text)
                if title_match:
                    result["course_name"] = title_match.group(1).strip()

            lecturer_match = re.search(r"מרצה[:\s]+([^\n]+)", details_text)
            if lecturer_match:
                result["lecturer"] = lecturer_match.group(1).strip()

            department_match = re.search(r"מחלקה[:\s]+([^\n]+)", details_text)
            if department_match:
                result["department"] = department_match.group(1).strip()

            semester_match = re.search(r"(סמסטר\s+[א-ת]\'?)", details_text)
            if semester_match:
                result["semester"] = semester_match.group(1).strip()
            
            try:
                # Preferred path: dedicated syllabus link/page.
                syllabus_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'סילבוס') or contains(text(), 'Syllabus') or contains(text(), 'צפייה')]"))
                )

                main_window = driver.current_window_handle
                syllabus_link.click()
                time.sleep(3)

                # Switch to new window if opened
                if len(driver.window_handles) > 1:
                    for handle in driver.window_handles:
                        if handle != main_window:
                            driver.switch_to.window(handle)
                            break

                syllabus_text = driver.find_element(By.TAG_NAME, 'body').text
                result["syllabus_text"] = syllabus_text
                result["topics"] = extract_weekly_topics(syllabus_text)
                result["found"] = True
            except TimeoutException:
                # Fallback: many courses embed rich syllabus-like text directly on details page.
                fallback_text = details_text or driver.find_element(By.TAG_NAME, 'body').text
                if len(fallback_text) > 300 and any(k in fallback_text for k in ["תאור הקורס", "תכנית הוראה", "סילבוס"]):
                    result["syllabus_text"] = fallback_text
                    result["topics"] = extract_weekly_topics(fallback_text)
                    result["found"] = True
                else:
                    result["errors"].append("Syllabus link not found on details page")
        else:
            result["errors"].append("No course details link found")
            
    except Exception as e:
        print(f"Error fetching syllabus for {course_num}: {e}")
        import traceback
        traceback.print_exc()
        result["errors"].append(str(e))
    finally:
        driver.quit()
        
    return result

if __name__ == "__main__":
    # Quick local test
    import sys
    test_course = sys.argv[1] if len(sys.argv) > 1 else "89-110" # Intro to CS
    print(f"Testing syllabus extraction for {test_course}...")
    res = get_course_syllabus(test_course, headless=True)
    if res["found"]:
        print(f"Found syllabus! Topics extracted: {len(res['topics'])}")
        for t in res["topics"][:5]: # Show first 5
            print(f"  Week {t['week']}: {t['topic']}")
    else:
        print("Syllabus not found.")
