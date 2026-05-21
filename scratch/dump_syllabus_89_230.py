import json

with open("data/raw/syllabuses.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for d in data:
    if d.get("course_num") == "89-230":
        with open("scratch/syllabus_text_89_230.txt", "w", encoding="utf-8") as out:
            out.write(d.get("syllabus_text", ""))
        break
