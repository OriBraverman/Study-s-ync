import os
from datetime import date
from src.schemas.models import StudentInputSchema
from src.orchestration.graph import run_pipeline

# Ensure we use the mock LLM for local predictable execution
os.environ["USE_MOCK_LLM"] = "true"

def main():
    student_input = StudentInputSchema(
        student_name="Danny Israely",
        course_name="מבוא להסתברות ולסטטיסטיקה",
        course_num="89-230",
        absence_start=date(2025, 10, 15),
        absence_end=date(2025, 11, 28)
    )

    print("=" * 60)
    print("Study[S]ync - Missed Topics & Plan Generation Verification")
    print("=" * 60)
    print(f"Course: {student_input.course_name} ({student_input.course_num})")
    print(f"Absence: {student_input.absence_start} to {student_input.absence_end}")
    print()

    plan = run_pipeline(student_input)
    print("SUCCESS: Pipeline executed successfully!")
    print(f"Course Name      : {plan.course_name}")
    print(f"Course Num       : {plan.course_num}")
    print(f"Total Days       : {plan.total_days}")
    print(f"Total Hours      : {plan.total_hours}")
    print(f"Study Tasks Count: {len(plan.study_tasks)}")
    print()
    print("Study Tasks:")
    for task in plan.study_tasks:
        print(f"  - Day {task.day}: {task.topic}")
        print(f"    Estimated Hours: {task.estimated_hours}")
        print(f"    Priority       : {task.priority}")
        print(f"    Citations      : {[c.source_name for c in task.citations]}")
    print("=" * 60)

if __name__ == "__main__":
    main()
