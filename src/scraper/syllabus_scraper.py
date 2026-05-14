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

def _extract_schedule_section(text):
    """Find the schedule/topics section in the syllabus text."""
    start_markers = [
        r'תכנית\s*הלימודים',
        r'נושאי\s*הקורס',
        r'Lessons?\s*plan',
        r'Schedule',
        r'Topics',
        r'סילבוס',
        r'Syllabus',
    ]

    lines = text.split('\n')
    start_idx = None
    for i, line in enumerate(lines):
        for marker in start_markers:
            if re.search(marker, line, re.IGNORECASE):
                start_idx = i
                break
        if start_idx is not None:
            break

    if start_idx is None:
        return text

    end_markers = [
        'מטרות הקורס',
        'ציון סופי',
        'דרישות הקורס',
        'ביבליוגרפיה',
        'Learning objectives',
        'Final grade',
        'Course requirements',
        'Bibliography',
        '* There may be changes',
        '** ייתכנו שינויים בסילבוס',
    ]

    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        for em in end_markers:
            if stripped.startswith(em):
                end_idx = i
                break
        if end_idx < len(lines):
            break

    return '\n'.join(lines[start_idx:end_idx])


def extract_weekly_topics(syllabus_text):
    """
    Heuristically extract weekly topics from the syllabus text.
    Handles both list formats ("1. Topic") and table formats where
    lesson numbers are followed by dates and multi-line topics.
    """
    topics = []

    schedule_text = _extract_schedule_section(syllabus_text)

    # Known junk / table-header lines to skip
    skip_lines = {
        'lesson no.', 'topic', 'active learning', 'required reading', 'assessment',
        'נושא', 'למידה פעילה', 'קריאה נדרשת', 'הערכה', "מס'", 'השיעור',
        'abacus outline lessons plan (including active learning):',
        'abacus outline',
        'additional topics', 'if time permits',
    }

    # Section headers that end the schedule
    end_headers = {
        'מטרות הקורס / תוצרי הלמידה',
        'learning objectives',
        'ציון סופי',
        'final grade',
        'דרישות הקורס',
        'course requirements',
        'ביבליוגרפיה',
        'bibliography',
        '* there may be changes in the syllabus depending on learning progress and effectiveness',
        '** ייתכנו שינויים בסילבוס בהתאם לקצב ההתקדמות ואפקטיביות הלמידה',
        'correctness of functional programs',
        'axiomatic semantics',
        'formal verification',
        'primitive recursive functions',
    }

    lines = [line.strip() for line in schedule_text.split('\n')]

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue

        lower = line.lower()
        if lower in skip_lines:
            i += 1
            continue

        # End of schedule section
        if lower in end_headers or any(line.startswith(h) for h in end_headers if len(h) > 10):
            break

        # Pattern A: explicit week/lesson label
        week_match = re.match(r'^(?:שבוע|מפגש|Week|Lesson)\s*(\d+)[:.-]?\s*(.*)', line, re.IGNORECASE)
        if week_match:
            week_num = week_match.group(1)
            topic_desc = week_match.group(2).strip()
            if topic_desc:
                topics.append({"week": week_num, "topic": topic_desc})
            else:
                i += 1
                parts = []
                while i < len(lines) and lines[i] and not re.match(r'^(?:שבוע|מפגש|Week|Lesson)\s*\d+', lines[i], re.IGNORECASE):
                    if lines[i].lower() in skip_lines or lines[i].lower() in end_headers:
                        break
                    if re.match(r'^\d{1,2}$', lines[i]):
                        i -= 1
                        break
                    parts.append(lines[i])
                    i += 1
                if parts:
                    topics.append({"week": week_num, "topic": " ".join(parts)})
            i += 1
            continue

        # Pattern B: standalone number 1-30 that looks like a lesson number
        if re.match(r'^\d{1,2}$', line) and 1 <= int(line) <= 30:
            week_num = line
            i += 1

            # Skip empty lines
            while i < len(lines) and not lines[i]:
                i += 1

            # Skip date line (DD.MM.YY or DD/MM/YY)
            if i < len(lines) and re.match(r'^\d{1,2}[./]\d{1,2}[./]\d{2,4}$', lines[i]):
                i += 1
                while i < len(lines) and not lines[i]:
                    i += 1

            # Collect topic lines
            parts = []
            while i < len(lines):
                curr = lines[i]
                if not curr:
                    i += 1
                    continue

                # Stop at next standalone lesson number
                if re.match(r'^\d{1,2}$', curr) and 1 <= int(curr) <= 30:
                    i -= 1
                    break

                # Stop at explicit week labels
                if re.match(r'^(?:שבוע|מפגש|Week|Lesson)\s*\d+', curr, re.IGNORECASE):
                    i -= 1
                    break

                # Stop at section headers
                if curr.lower() in end_headers or any(curr.startswith(h) for h in end_headers if len(h) > 10):
                    i -= 1
                    break

                # Skip table column headers
                if curr.lower() in skip_lines:
                    i += 1
                    continue

                # Skip inline dates
                if re.match(r'^\d{1,2}[./]\d{1,2}[./]\d{2,4}$', curr):
                    i += 1
                    continue

                # Heuristic: stop at lines that look like reading assignments / assessments
                if re.match(r'^(Chapter|Chapters|Home\s+assignment|Home\s+work|Cornell|MIT |Notes\s+on)', curr, re.IGNORECASE):
                    i -= 1
                    break

                parts.append(curr)
                i += 1

            if parts:
                topic_text = " ".join(parts)
                topic_text = re.sub(r'\s+', ' ', topic_text).strip()
                # Filter junk
                if (len(topic_text) > 2 and
                    not topic_text.startswith('**') and
                    topic_text not in ('למידה בקבוצות/ מרצה אורח.ת',)):
                    topics.append({"week": week_num, "topic": topic_text})
            i += 1
            continue

        # Pattern C: numbered list with topic on same line (old behavior preserved)
        list_match = re.match(r'^(\d+)[\s.)-](?!.*\d{1,2}[./]\d{1,2}[./]\d{2,4})(.+)', line)
        if list_match:
            week_num = list_match.group(1)
            topic_desc = list_match.group(2).strip()
            if topic_desc and topic_desc not in ('למידה בקבוצות/ מרצה אורח.ת',):
                topics.append({"week": week_num, "topic": topic_desc})
            i += 1
            continue

        i += 1

    # Deduplicate consecutive identical entries
    seen = set()
    deduped = []
    for t in topics:
        key = (t['week'], t['topic'])
        if key not in seen and t['topic']:
            seen.add(key)
            deduped.append(t)

    return deduped

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
