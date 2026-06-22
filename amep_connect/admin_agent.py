from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Simulated student progress data (in a real app, this would be a database)
student_progress = {
    "student_001": {"word_order": 3, "spelling": 2, "grammar": 5, "register": 1},
    "student_002": {"word_order": 1, "spelling": 4, "grammar": 3, "register": 0},
}

def track_progress(student_id: str, new_errors: dict) -> dict:
    """
    Updates student progress and returns competency report.
    """
    # Initialize student if not exists
    if student_id not in student_progress:
        student_progress[student_id] = {"word_order": 0, "spelling": 0, "grammar": 0, "register": 0}
    
    # Update with new errors (simplified - in reality, would store history)
    for error_type, count in new_errors.items():
        if error_type in student_progress[student_id]:
            student_progress[student_id][error_type] += count
    
    # Generate competency report
    report = {
        "student_id": student_id,
        "total_errors": sum(student_progress[student_id].values()),
        "areas_needing_improvement": [],
        "cswe_level": "CSWE II"
    }
    
    # Determine improvement areas
    for error_type, count in student_progress[student_id].items():
        if count > 2:
            report["areas_needing_improvement"].append(error_type)
    
    # Determine CSWE level (simplified)
    if report["total_errors"] < 5:
        report["cswe_level"] = "CSWE III (Functional English)"
    elif report["total_errors"] < 15:
        report["cswe_level"] = "CSWE II (Developing English)"
    else:
        report["cswe_level"] = "CSWE I (Beginner English)"
    
    return report

# Create the Admin Portal Agent
admin_agent = Agent(
    name="admin_agent",
    description="Tracks student progress and generates competency reports for educators",
    model="gemini-2.0-flash",
    instruction="""
    You are an Admin Portal Agent for AMEP Connect.
    Your role is to track student progress and generate reports for educators.
    
    Use the track_progress tool to:
    - Update student error profiles
    - Track progress over time
    - Generate CSWE level competency reports
    - Identify areas needing improvement
    
    Reports should be clear and actionable for educators.
    """,
    tools=[FunctionTool(track_progress)]
)