from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from diagnostic_agent import diagnostic_agent
from scaffolding_agent import scaffolding_agent
from admin_agent import admin_agent

# Create the orchestrator agent
orchestrator_agent = Agent(
    name="amep_orchestrator",
    description="AMEP Connect Master Agent - coordinates diagnostic, scaffolding, and admin agents",
    model="gemini-2.0-flash",
    instruction="""
    You are the AMEP Connect Orchestrator Agent.
    Your role is to coordinate the three specialized agents:
    
    1. Diagnostic Agent: Analyzes student submissions for errors
    2. Scaffolding Agent: Provides personalized learning interventions
    3. Admin Portal Agent: Tracks progress and generates reports
    
    Workflow:
    1. Receive student submission (text)
    2. Send to Diagnostic Agent → get error profile
    3. Send error profile to Scaffolding Agent → get interventions
    4. Update Admin Portal Agent → track progress
    5. Return combined response to student
    
    Always be encouraging and supportive!
    """,
    sub_agents=[diagnostic_agent, scaffolding_agent, admin_agent]
)

# This is the root_agent that ADK expects
root_agent = orchestrator_agent

# Test function to simulate the workflow
def test_orchestrator():
    """
    Simulates the complete workflow without running the server.
    """
    # Simulate a student submission
    student_text = "I going to the shop yestaday and I buyed milk"
    student_id = "test_student_001"
    
    print("=" * 50)
    print("AMEP CONNECT - WORKFLOW SIMULATION")
    print("=" * 50)
    print(f"\n📝 Student Submission: '{student_text}'")
    print(f"👤 Student ID: {student_id}")
    print("\n--- Step 1: Diagnostic Agent ---")
    
    # Step 1: Diagnose errors
    from diagnostic_agent import analyze_text
    errors = analyze_text(student_text)
    print(f"🔍 Error Profile: {errors}")
    
    print("\n--- Step 2: Scaffolding Agent ---")
    
    # Step 2: Generate interventions
    from scaffolding_agent import generate_scaffolding
    interventions = generate_scaffolding(errors)
    print("📚 Recommended Interventions:")
    for category, items in interventions.items():
        if items:
            print(f"  {category.upper()}:")
            for item in items:
                print(f"    {item}")
    
    print("\n--- Step 3: Admin Portal Agent ---")
    
    # Step 3: Update progress
    from admin_agent import track_progress
    report = track_progress(student_id, errors)
    print(f"📊 Progress Report for {student_id}:")
    print(f"  Total Errors: {report['total_errors']}")
    print(f"  Areas Needing Improvement: {report['areas_needing_improvement']}")
    print(f"  CSWE Level: {report['cswe_level']}")
    
    print("\n✨ Workflow completed successfully!")

if __name__ == "__main__":
    test_orchestrator()