import json
import math
import os
import random
import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from syllabus_scraper import get_course_syllabus, setup_driver, wait_for_search_form


OUTPUT_PATH = "data/raw/syllabuses.json"
LEGACY_PATH = "src/data/raw/syllabuses.json"
GRID_POSTBACK_TARGET = "ctl00$ContentPlaceHolder1$gvLessons"
CS_DEPARTMENT_SEARCH_TERM = "המחלקה למדעי המחשב"
CS_DEPARTMENT_FALLBACK_VALUE = "84"


def normalize_code(raw_code):
    code = raw_code.strip().replace("-", "")
    if not code.startswith("89"):
        return None
    if len(code) < 5:
        return None
    return f"{code[:2]}-{code[2:]}"


def _extract_total_courses(body_text):
    match = re.search(r"([\d,]+)\s+קורסים ברשימה", body_text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _extract_codes_from_table_text(table_text):
    codes = set()
    for raw in re.findall(r"\b89\d{3,5}\b", table_text):
        norm = normalize_code(raw)
        if norm:
            codes.add(norm)
    return codes


def _find_total_pages(driver, estimated_pages):
    """
    Jump to last page and derive the real last-page number from pager cells.
    Fallback to estimated_pages when pager parsing fails.
    """
    try:
        last_link = driver.find_element(By.LINK_TEXT, ">>")
        last_link.click()
        time.sleep(2)

        pager_cells = driver.find_elements(By.CSS_SELECTOR, "#ContentPlaceHolder1_gvLessons td table td")
        page_numbers = []
        for cell in pager_cells:
            text = (cell.text or "").strip()
            if text.isdigit():
                page_numbers.append(int(text))

        if page_numbers:
            return max(page_numbers)
    except Exception:
        pass

    return estimated_pages


def _go_to_page(driver, page_number):
    script = (
        "if (window.__doPostBack) { "
        f"__doPostBack('{GRID_POSTBACK_TARGET}','Page${page_number}');"
        " }"
    )
    driver.execute_script(script)


def _select_cs_department_and_search(driver, search_term=CS_DEPARTMENT_SEARCH_TERM):
    """
    Open results while explicitly filtering to the CS department.
    Fallback path keeps progress moving if portal labels are changed.
    """
    department_selected = False

    try:
        department_select = Select(driver.find_element(By.ID, "ContentPlaceHolder1_cmbDepartments"))

        # Prefer exact term requested by user.
        normalized_target = search_term.replace("ה", "", 1).strip()
        options = [opt.text.strip() for opt in department_select.options if opt.text]

        exact = next((opt for opt in options if opt == search_term), None)
        if exact:
            department_select.select_by_visible_text(exact)
            department_selected = True
        else:
            # Site currently uses "המחלקה למדעי המחשב" or variant without leading ה.
            contains = next(
                (
                    opt
                    for opt in options
                    if "מדעי המחשב" in opt and normalized_target in opt.replace("ה", "", 1)
                ),
                None,
            )
            if contains:
                department_select.select_by_visible_text(contains)
                department_selected = True
            else:
                department_select.select_by_value(CS_DEPARTMENT_FALLBACK_VALUE)
                department_selected = True
    except Exception:
        department_selected = False

    if not department_selected:
        # Last-resort fallback: push the requested term into name search.
        try:
            name_input = driver.find_element(By.ID, "ContentPlaceHolder1_txLessonName")
            name_input.clear()
            name_input.send_keys(search_term)
        except Exception:
            pass

    driver.find_element(By.ID, "ContentPlaceHolder1_btnSearch").click()
    time.sleep(2.2)


def _open_cs_courses_grid(driver):
    driver.get("https://courses.biu.ac.il/")
    wait_for_search_form(driver, timeout=60)
    _select_cs_department_and_search(driver)


def _get_grid_text_with_recovery(driver, page_number, retries=3):
    for attempt in range(1, retries + 1):
        try:
            grid = driver.find_element(By.CSS_SELECTOR, "#ContentPlaceHolder1_gvLessons")
            return grid.text
        except Exception:
            if attempt == retries:
                raise

            # Challenge/interstitial occasionally interrupts pagination.
            # Recover by re-opening the full listing and returning to the target page.
            _open_cs_courses_grid(driver)
            if page_number > 1:
                _go_to_page(driver, page_number)
                time.sleep(1.5)


def discover_cs_courses(headless=True):
    driver = setup_driver(headless=headless)
    discovered = set()

    try:
        _open_cs_courses_grid(driver)

        body_text = driver.find_element(By.TAG_NAME, "body").text
        total_courses = _extract_total_courses(body_text) or 0

        # Grid seems to show ~20 rows per page, this gives a stable upper bound fallback.
        estimated_pages = max(1, int(math.ceil(total_courses / 20))) if total_courses else 1
        total_pages = _find_total_pages(driver, estimated_pages)

        print(f"Discovered total course groups for '{CS_DEPARTMENT_SEARCH_TERM}': {total_courses}")
        print(f"Traversing {total_pages} pages to collect prefix-89 courses...")

        # Return to first page before deterministic page iteration.
        _go_to_page(driver, 1)
        time.sleep(1.5)

        for page in range(1, total_pages + 1):
            page_done = False
            last_error = None

            for attempt in range(1, 5):
                try:
                    if page > 1:
                        _go_to_page(driver, page)
                        time.sleep(1.2)

                    table_text = _get_grid_text_with_recovery(driver, page_number=page, retries=3)
                    discovered.update(_extract_codes_from_table_text(table_text))
                    page_done = True
                    break
                except Exception as exc:
                    last_error = exc
                    print(f"  Warning: page {page} attempt {attempt} failed ({exc}). Restarting browser...")
                    try:
                        driver.quit()
                    except Exception:
                        pass

                    driver = setup_driver(headless=headless)
                    _open_cs_courses_grid(driver)
                    if page > 1:
                        _go_to_page(driver, page)
                        time.sleep(1.5)

            if not page_done:
                raise RuntimeError(f"Failed to load listing page {page} after retries") from last_error

            if page % 25 == 0 or page == total_pages:
                print(f"  Progress: page {page}/{total_pages}, unique 89* codes: {len(discovered)}")

            # Polite pacing for listing traversal.
            time.sleep(0.3)

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return sorted(discovered)


def load_existing_records():
    for path in (OUTPUT_PATH, LEGACY_PATH):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    return []


def write_records(records):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)


def scrape_with_retries(course_num, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        result = get_course_syllabus(course_num, headless=True)
        if result.get("found"):
            return result

        errors = [str(e) for e in result.get("errors", [])]
        if any(
            msg in " | ".join(errors)
            for msg in (
                "Syllabus link not found on details page",
                "No course details link found",
            )
        ):
            # Deterministic page-content outcome; additional retries won't help.
            return result

        # Backoff for flaky network/challenge windows.
        sleep_s = min(10, 2 * attempt + random.uniform(0.2, 0.9))
        print(f"    Attempt {attempt}/{max_attempts} failed for {course_num}; retrying in {sleep_s:.1f}s")
        time.sleep(sleep_s)

    return result


def validate_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Output JSON must be a list")
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"Row {i} is not an object")
        for required in ("course_num", "found", "syllabus_text", "topics"):
            if required not in row:
                raise ValueError(f"Row {i} is missing required field: {required}")
    return data


def run_pipeline():
    existing = load_existing_records()
    existing_by_course = {item.get("course_num"): item for item in existing if isinstance(item, dict)}

    all_cs_courses = discover_cs_courses(headless=True)
    print(f"Total unique Computer Science codes (prefix 89) discovered: {len(all_cs_courses)}")

    # Dedup logic: skip only records that already exist and are already found.
    # Re-scrape existing non-found records to improve completeness.
    to_scrape = []
    for course_num in all_cs_courses:
        prev = existing_by_course.get(course_num)
        if prev and prev.get("found") is True:
            continue
        to_scrape.append(course_num)

    print(f"Courses queued for scraping (after dedupe): {len(to_scrape)}")

    new_records = []
    for idx, course_num in enumerate(to_scrape, start=1):
        print(f"[{idx}/{len(to_scrape)}] Scraping syllabus for {course_num}...")
        res = scrape_with_retries(course_num, max_attempts=3)

        if res.get("found"):
            print(f"  [SUCCESS] Found syllabus, extracted {len(res.get('topics', []))} topics")
        else:
            print("  [NOT FOUND] Syllabus page unavailable or blocked")

        new_records.append(res)

        # Polite pacing between requests.
        time.sleep(random.uniform(1.2, 2.4))

    # Merge by course_num while preserving latest scrape result for updated courses.
    merged_by_course = {}
    for row in existing:
        if isinstance(row, dict) and row.get("course_num"):
            merged_by_course[row["course_num"]] = row
    for row in new_records:
        if isinstance(row, dict) and row.get("course_num"):
            merged_by_course[row["course_num"]] = row

    merged = [merged_by_course[key] for key in sorted(merged_by_course.keys())]
    write_records(merged)
    validated = validate_json(OUTPUT_PATH)

    found_count = sum(1 for x in validated if x.get("course_num", "").startswith("89-") and x.get("found"))
    print(f"\nPipeline complete. JSON records: {len(validated)}")
    print(f"Prefix-89 records with found syllabuses: {found_count}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_pipeline()
