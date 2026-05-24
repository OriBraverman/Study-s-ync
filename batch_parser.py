import os
import json
import shutil
import subprocess
import tempfile
import io

import fitz          # PyMuPDF     — pip install pymupdf
import pytesseract   # OCR         — pip install pytesseract  (+ apt install tesseract-ocr)
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

# ─────────────────────────────────────────────────────────
#  תיקיות
# ─────────────────────────────────────────────────────────
INPUT_FOLDER  = "raw_files"
OUTPUT_FOLDER = os.path.join("data", "json_outputs")   # << data/json_outputs


# ─────────────────────────────────────────────────────────
#  עזרים: חילוץ טקסט מ-shape (python-pptx)
# ─────────────────────────────────────────────────────────
FOOTER_KEYWORDS = {"date placeholder", "footer placeholder", "slide number placeholder"}

def is_footer_shape(shape):
    return any(kw in shape.name.lower() for kw in FOOTER_KEYWORDS)

def extract_texts_from_shape(shape):
    if is_footer_shape(shape):
        return []
    texts = []
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for child in shape.shapes:
            texts.extend(extract_texts_from_shape(child))
        return texts
    if shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                t = cell.text.strip()
                if t:
                    texts.append(t)
        return texts
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            t = "".join(run.text for run in para.runs).strip()
            if t:
                texts.append(t)
    return texts


def get_pptx_structure(file_path):
    """מחזיר מידע מבני לכל שקופית: כותרת + הערות דובר."""
    prs = Presentation(file_path)
    slides_meta = []
    for i, slide in enumerate(prs.slides):
        title = None
        if slide.shapes.title and slide.shapes.title.has_text_frame:
            title = slide.shapes.title.text.strip() or None
        notes = None
        if slide.has_notes_slide:
            nf = slide.notes_slide.notes_text_frame
            if nf and nf.text.strip():
                notes = nf.text.strip()
        slides_meta.append({"title": title, "speaker_notes": notes})
    return slides_meta


# ─────────────────────────────────────────────────────────
#  המרת PPTX → PDF עם LibreOffice
# ─────────────────────────────────────────────────────────
def convert_pptx_to_pdf(pptx_path, tmp_dir):
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "pdf",
         "--outdir", tmp_dir, pptx_path],
        capture_output=True, text=True
    )
    base = os.path.splitext(os.path.basename(pptx_path))[0]
    pdf_path = os.path.join(tmp_dir, base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"LibreOffice המרה נכשלה:\n{result.stderr}")
    return pdf_path


# ─────────────────────────────────────────────────────────
#  OCR של עמוד PDF → טקסט נקי
# ─────────────────────────────────────────────────────────
FOOTER_NOISE = {"algorithms and ds i: sorting", "april", "april  2025", "april 2025"}

def clean_ocr_lines(raw_text):
    lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # הסר כותרת תחתונה/מספר עמוד
        low = stripped.lower()
        if any(low.startswith(noise) or low == noise for noise in FOOTER_NOISE):
            continue
        if stripped.isdigit() and len(stripped) <= 2:
            continue
        lines.append(stripped)
    return "\n".join(lines)


def ocr_pdf_pages(pdf_path, dpi=200):
    """מחזיר רשימה של טקסט OCR לכל עמוד."""
    doc = fitz.open(pdf_path)
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)
    pages_ocr = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        raw = pytesseract.image_to_string(img, lang="eng")
        pages_ocr.append(clean_ocr_lines(raw))
    doc.close()
    return pages_ocr


# ─────────────────────────────────────────────────────────
#  עיבוד PPTX מלא
# ─────────────────────────────────────────────────────────
def process_pptx(file_path):
    with tempfile.TemporaryDirectory() as tmp_dir:
        # שלב 1: מבנה (כותרות + הערות)
        slides_meta = get_pptx_structure(file_path)

        # שלב 2: המרה ל-PDF ו-OCR
        pdf_path = convert_pptx_to_pdf(file_path, tmp_dir)
        pages_ocr = ocr_pdf_pages(pdf_path, dpi=200)

    # שלב 3: שילוב
    slides_data = []
    for i, meta in enumerate(slides_meta):
        content = pages_ocr[i] if i < len(pages_ocr) else ""
        slides_data.append({
            "page_number": i + 1,
            "title": meta["title"],
            "content": content,
            "speaker_notes": meta["speaker_notes"]
        })
    return slides_data


# ─────────────────────────────────────────────────────────
#  עיבוד PDF
# ─────────────────────────────────────────────────────────
def process_pdf(file_path):
    doc = fitz.open(file_path)
    pages_data = []
    for i, page in enumerate(doc):
        # ניסיון ראשון: חילוץ טקסט ישיר (מהיר יותר)
        text = page.get_text("text").strip()
        if len(text) < 50:
            # עמוד עם תמונות → OCR
            scale = 200 / 72.0
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="eng").strip()
        if text:
            pages_data.append({"page_number": i + 1, "content": text})
    doc.close()
    return pages_data


# ─────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────
def main():
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"נוצרה תיקייה '{INPUT_FOLDER}'. שים בה קבצי PDF/PPTX והרץ שוב.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    files = [f for f in os.listdir(INPUT_FOLDER)
             if os.path.isfile(os.path.join(INPUT_FOLDER, f))]

    if not files:
        print(f"לא נמצאו קבצים ב-'{INPUT_FOLDER}'.")
        return

    print(f"נמצאו {len(files)} קבצים — מתחיל עיבוד...\n")
    processed = skipped = 0

    for file_name in files:
        file_path = os.path.join(INPUT_FOLDER, file_name)
        base_name, ext = os.path.splitext(file_name)
        ext = ext.lower()

        print(f"⏳ מעבד: {file_name}")
        try:
            if ext == ".pptx":
                parsed_data = process_pptx(file_path)
            elif ext == ".pdf":
                parsed_data = process_pdf(file_path)
            else:
                print(f"  ⚠️  סוג קובץ לא נתמך — מדולג.")
                skipped += 1
                continue
        except Exception as e:
            print(f"  ❌ שגיאה: {e}")
            skipped += 1
            continue

        if not parsed_data:
            print(f"  ⚠️  לא נמצא תוכן.")
            skipped += 1
            continue

        out_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {base_name}.json ({len(parsed_data)} עמודים)")
        processed += 1

    print(f"\nסיום! עובדו {processed}, דולגו {skipped}.")
    print(f"התוצאות נמצאות ב: {OUTPUT_FOLDER}/")


if __name__ == "__main__":
    main()