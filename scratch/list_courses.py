import json

with open("data/raw/syllabuses.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
for d in data:
    course_num = d.get("course_num", "")
    course_name = d.get("course_name", "")
    found = d.get("found", False)
    lines.append(f"{course_num} | {course_name} | found={found}")

with open("scratch/courses_list.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(lines))
