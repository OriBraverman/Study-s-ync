import json

with open("data/raw/syllabuses.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for d in data:
    if d.get("course_num") == "89-230":
        out_content = []
        out_content.append(f"Course Num: {d.get('course_num')}")
        out_content.append(f"Course Name: {d.get('course_name')}")
        out_content.append(f"Found: {d.get('found')}")
        out_content.append(f"Syllabus Text Length: {len(d.get('syllabus_text', ''))}")
        out_content.append("Topics:")
        out_content.append(json.dumps(d.get("topics", []), ensure_ascii=False, indent=2))
        
        with open("scratch/inspect_89_230.txt", "w", encoding="utf-8") as out:
            out.write("\n".join(out_content))
        break
