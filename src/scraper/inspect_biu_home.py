import re
import time
import requests

URL = "https://courses.biu.ac.il/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}


def fetch_html(max_attempts=8):
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(URL, headers=HEADERS, timeout=40)
            if resp.status_code == 200 and len(resp.text) > 1000:
                return resp.text
            print(f"Attempt {attempt}: status={resp.status_code}, len={len(resp.text)}")
        except Exception as exc:
            print(f"Attempt {attempt} failed: {exc}")
        time.sleep(2)
    raise RuntimeError("Failed to fetch BIU page")


def main():
    html = fetch_html()
    print("len:", len(html))

    needles = [
        "LessonCode",
        "CourseDetails",
        "btnSearch",
        "Search",
        "syllabus",
        "סילבוס",
        "txLesson",
        "ContentPlaceHolder1_",
    ]
    for needle in needles:
        print(f"{needle}:", html.find(needle))

    ids = sorted(set(re.findall(r'id="([^"]+)"', html)))
    print("ids_count:", len(ids))
    for item in ids:
        low = item.lower()
        if any(k in low for k in ["search", "course", "lesson", "syll", "query", "subject", "code"]):
            print(item)

    print("\nPotential input fields:")
    for match in re.finditer(r'<input[^>]+>', html, re.IGNORECASE):
        tag = match.group(0)
        low = tag.lower()
        if any(k in low for k in ["search", "course", "lesson", "code", "subject"]):
            print(tag[:240])


if __name__ == "__main__":
    main()
