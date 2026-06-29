from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def generate_scaffolding(errors: dict, student_text: str = "") -> dict:
    """
    Generates personalized exercises based on the SPECIFIC errors found.
    """
    interventions = {
        "word_order": [],
        "spelling": [],
        "grammar": [],
        "register": []
    }
    
    # --- WORD ORDER: Check what specific word order error occurred ---
    if errors.get("word_order", 0) > 0:
        # Check for missing "am/is/are" before "going"
        if "going" in student_text.lower() and "am going" not in student_text.lower() and "is going" not in student_text.lower():
            interventions["word_order"] = [
                "🔹 You wrote 'going' without 'am/is/are'. This is a common error.",
                "📝 Correction: 'I am going' or 'She is going'",
                "🔹 Try: 'I ____ going to the shop.' (Fill in: am)",
                "🔹 Write 3 sentences using 'am going', 'is going', and 'are going'."
            ]
        # Check for subject-verb agreement issues
        elif errors.get("word_order", 0) > 0:
            interventions["word_order"] = [
                "🔹 Word Order: Your sentence structure needs attention.",
                "📝 Remember: Subject + Verb + Object",
                "🔹 Example: 'I buy milk' not 'I buyed milks'",
                "🔹 Write 3 correct sentences about daily activities."
            ]
    
    # --- SPELLING: Check what specific spelling errors occurred ---
    if errors.get("spelling", 0) > 0:
        spelling_errors = []
        
        # Check for specific misspellings in the student's text
        text_lower = student_text.lower()
        
        if "yestaday" in text_lower:
            spelling_errors.append(("yestaday", "yesterday"))
        if "tommorow" in text_lower:
            spelling_errors.append(("tommorow", "tomorrow"))
        if "buyed" in text_lower or "buyd" in text_lower:
            spelling_errors.append(("buyed", "bought"))
        if "definately" in text_lower:
            spelling_errors.append(("definately", "definitely"))
        if "thi" in text_lower:
            spelling_errors.append(("thi", "this"))
        if "milks" in text_lower:
            spelling_errors.append(("milks", "milk" if "milks" in text_lower else ""))
        
        if spelling_errors:
            interventions["spelling"] = ["🔹 Spelling corrections for your text:"]
            for wrong, correct in spelling_errors:
                if correct:
                    interventions["spelling"].append(f"   • '{wrong}' → should be '{correct}'")
            interventions["spelling"].append("🔹 Write each corrected word 3 times.")
        else:
            interventions["spelling"] = [
                "🔹 Spelling Practice: Find the correct spelling:",
                "   'definately' or 'definitely'?",
                "   Answer: 'definitely' - remember it has 'finite' in it!",
                "🔹 Write the word 'definitely' three times."
            ]
    
    # --- GRAMMAR: Check what specific grammar issues occurred ---
    if errors.get("grammar", 0) > 0:
        grammar_fixes = []
        text_lower = student_text.lower()
        
        if "buyed" in text_lower:
            grammar_fixes.append("🔹 'buyed' → use 'bought' (irregular verb)")
            grammar_fixes.append("📝 Irregular verbs don't add -ed: buy-bought-bought")
            grammar_fixes.append("🔹 Write: 'Yesterday I ________ milk.' (Answer: bought)")
        
        if "milks" in text_lower:
            grammar_fixes.append("🔹 'milks' → use 'milk' (uncountable noun)")
            grammar_fixes.append("📝 Some nouns don't have a plural form: milk, water, rice")
            grammar_fixes.append("🔹 Write: 'I need some ________.' (Answer: milk)")
        
        if "going to the shop" in text_lower and "the" in text_lower:
            # This is actually correct, but we'll add a practice
            grammar_fixes.append("🔹 Good use of 'the'! Keep practicing articles.")
        
        if not grammar_fixes:
            # Fallback generic grammar
            grammar_fixes = [
                "🔹 Article Practice: 'I went to ___ shop and bought ___ apples.'",
                "   Answers: 'the' and 'some'",
                "🔹 Write a sentence using 'a', 'an', and 'the'."
            ]
        
        interventions["grammar"] = grammar_fixes
    
    # --- REGISTER: Check for informal language ---
    if errors.get("register", 0) > 0:
        interventions["register"] = [
            "🔹 You're using informal language in a formal context.",
            "📝 Instead of 'gonna', use 'going to'",
            "📝 Instead of 'wanna', use 'want to'",
            "🔹 Rewrite your sentence using formal language."
        ]
    
    # --- If NO errors found ---
    if all(len(v) == 0 for v in interventions.values()):
        interventions["positive"] = [
            "🌟 Great job! Your English looks strong.",
            "🔹 Try this challenge: Write a short paragraph about your weekend."
        ]
    
    return interventions

# Create the Scaffolding Agent
scaffolding_agent = Agent(
    name="scaffolding_agent",
    description="Provides personalized learning interventions based on specific diagnostic results",
    model="gemini-2.0-flash",
    instruction="""
    You are a Scaffolding Agent for AMEP Connect.
    Your role is to provide personalized learning interventions based on the specific errors found.
    
    Use the generate_scaffolding tool to create:
    - Sentence building exercises for word order issues
    - Spelling practice for specific misspelled words
    - Grammar exercises for specific grammar issues
    - Register awareness exercises for informal language
    
    Always be encouraging and positive. Adult learners need confidence!
    """,
    tools=[FunctionTool(generate_scaffolding)]
)