from src.schemas.models import StudentInputSchema
from src.orchestration.graph import run_pipeline

plan = run_pipeline(StudentInputSchema(
    student_name="Test User",
    course_name="Data Structures",
    course_num="89-120",
    absence_start="2026-03-01",
    absence_end="2026-03-10"
))

print("Planner Pipeline Output:")
print(f"Total tasks: {len(plan.study_tasks)}")
for task in plan.study_tasks:
    print(f"- {task.topic}: {task.description[:50]}...")
