import os
import json
from pptx import Presentation
from pypdf import PdfReader

# הגדרת שמות התיקיות
INPUT_FOLDER = "raw_files"
OUTPUT_FOLDER = "json_outputs"

def extract_text_from_pptx(file_path):
    """מחלץ טקסט מקובץ פאוורפוינט ומסדר לפי שקופיות"""
    try:
        prs = Presentation(file_path)
        slides_data = []
        for i, slide in enumerate(prs.slides):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            if slide_text:
                slides_data.append({
                    "page_number": i + 1,
                    "content": "\n".join(slide_text)
                })
        return slides_data
    except Exception as e:
        print(f"שגיאה בקריאת PPTX ({os.path.basename(file_path)}): {e}")
        return None

def extract_text_from_pdf(file_path):
    """מחלץ טקסט מקובץ PDF ומסדר לפי עמודים"""
    try:
        reader = PdfReader(file_path)
        pages_data = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_data.append({
                    "page_number": i + 1,
                    "content": text.strip()
                })
        return pages_data
    except Exception as e:
        print(f"שגיאה בקריאת PDF ({os.path.basename(file_path)}): {e}")
        return None

def main():
    # יצירת תיקיית קלט אם היא לא קיימת
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"נוצרה תיקייה חדשה בשם '{INPUT_FOLDER}'. שים בתוכה את קבצי ה-PDF וה-PPTX שלך והרץ שוב.")
        return

    # יצירת תיקיית פלט אם היא לא קיימת
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # מעבר על כל הקבצים בתיקיית הקלט
    files = os.listdir(INPUT_FOLDER)
    processed_count = 0

    print(f"נמצאו {len(files)} קבצים בתיקיית {INPUT_FOLDER}.\nמתחיל בעיבוד...")

    for file_name in files:
        file_path = os.path.join(INPUT_FOLDER, file_name)
        base_name, ext = os.path.splitext(file_name)
        ext = ext.lower()

        parsed_data = None

        # בדיקת סוג הקובץ והפעלה של ה-Parser המתאים
        if ext == '.pptx':
            parsed_data = extract_text_from_pptx(file_path)
        elif ext == '.pdf':
            parsed_data = extract_text_from_pdf(file_path)
        else:
            # מתעלם מקבצים אחרים (כמו קבצי מערכת או תמונות)
            continue

        if parsed_data:
            # יצירת שם קובץ ה-JSON החדש
            output_file_name = f"{base_name}.json"
            output_file_path = os.path.join(OUTPUT_FOLDER, output_file_name)

            # שמירה ל-JSON עם תמיכה מלאה בעברית
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=4)
            
            print(f"✅ קובץ עובד בהצלחה: {file_name} -> {output_file_name}")
            processed_count += 1

    print(f"\nהסתיים בהצלחה! עובדו {processed_count} קבצים. התוצרים מחכים בתיקייה '{OUTPUT_FOLDER}'.")

if __name__ == "__main__":
    main()