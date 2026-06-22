from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# This function generates scaffolding exercises based on error profile
def generate_scaffolding(errors: dict) -> dict:
    """
    Generates personalized exercises based on error profile.
    Returns a dictionary of interventions.
    """
    interventions = {
        "word_order": [],
        "spelling": [],
        "grammar": [],
        "register": []
    }
    
    # Generate interventions for each error type
    if errors.get("word_order", 0) > 0:
        interventions["word_order"] = [
            "🔹 Sentence Scrambler: Arrange these words into a correct sentence:",
            "   'shop / going / to / I / am / the'",
            "   Answer: 'I am going to the shop.'",
            "🔹 Try building your own sentence about going somewhere."
        ]
    
    if errors.get("spelling", 0) > 0:
        interventions["spelling"] = [
            "🔹 Spelling Practice: Find the correct spelling:",
            "   'definately' or 'definitely'?",
            "   Answer: 'definitely' - remember it has 'finite' in it!",
            "🔹 Write the word 'definitely' three times."
        ]
    
    if errors.get("grammar", 0) > 0:
        interventions["grammar"] = [
            "🔹 Article Practice: Fill in the blanks:",
            "   'I went to ___ shop and bought ___ apples.'",
            "   Answers: 'the' and 'some'",
            "🔹 Write a sentence using 'a', 'an', and 'the'."
        ]
    
    if errors.get("register", 0) > 0:
        interventions["register"] = [
            "🔹 Formal vs Informal: Which is more appropriate for a job application?",
            "   A: 'I wanna work here'",
            "   B: 'I would like to apply for this position'",
            "   Answer: B is more formal.",
            "🔹 Rewrite 'I'm gonna go' in formal language."
        ]
    
    # Add a general encouragement if no errors found
    if all(len(v) == 0 for v in interventions.values()):
        interventions["positive"] = [
            "🌟 Great job! Your English looks strong.",
            "🔹 Try this challenge: Write a short paragraph about your weekend."
        ]
    
    return interventions

# Create the Scaffolding Agent
scaffolding_agent = Agent(
    name="scaffolding_agent",
    description="Provides personalized learning interventions based on diagnostic results",
    model="gemini-2.0-flash",
    instruction="""
    You are a Scaffolding Agent for AMEP Connect.
    Your role is to provide personalized learning interventions based on error diagnostics.
    
    Use the generate_scaffolding tool to create:
    - Sentence building exercises for word order issues
    - Spelling practice for spelling errors
    - Article and verb tense practice for grammar issues
    - Register awareness exercises for informal language
    
    Always be encouraging and positive. Adult learners need confidence!
    """,
    tools=[FunctionTool(generate_scaffolding)]
)