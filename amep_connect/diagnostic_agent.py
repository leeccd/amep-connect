from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def analyze_text(text: str) -> dict:
    """
    Analyzes student text for common English errors.
    This function is called by the agent.
    """
    errors = {
        "word_order": 0,
        "spelling": 0,
        "grammar": 0,
        "register": 0,
        "confidence_score": 0.0
    }
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # --- WORD ORDER: Missing auxiliary verb before 'going' ---
    if "going" in text_lower:
        # Check if 'am/is/are' comes before 'going'
        # Simple check: if 'going' appears without 'am going', 'is going', 'are going'
        has_auxiliary = any(aux in text_lower for aux in ["am going", "is going", "are going"])
        if not has_auxiliary:
            errors["word_order"] += 1
    
    # --- SPELLING: Common misspellings ---
    misspellings = {
        "yestaday": "yesterday",
        "tommorow": "tomorrow",
        "definately": "definitely",
        "seperate": "separate",
        "recieve": "receive",
        "buyed": "bought",
        "buyd": "bought",
        "teh": "the",
        "thier": "their",
    }
    
    for word in words:
        if word in misspellings:
            errors["spelling"] += 1
    
    # --- GRAMMAR: Irregular past tense ---
    if "buyed" in text_lower or "buyd" in text_lower:
        errors["grammar"] += 1
    
    # --- GRAMMAR: Missing articles ---
    common_nouns = ["shop", "school", "work", "home", "hospital", "restaurant", "park", "city", "beach"]
    for noun in common_nouns:
        if noun in text_lower:
            # Check if noun appears without article
            # Simple: if 'the' or 'a' or 'an' doesn't appear before the noun
            # This is a simplified check
            if f"the {noun}" not in text_lower and f"a {noun}" not in text_lower and f"an {noun}" not in text_lower:
                errors["grammar"] += 1
                break  # Count once per submission for this type
    
    # --- REGISTER: Informal words ---
    informal = ["gonna", "wanna", "kinda", "sorta", "cuz", "coz", "lemme", "ain't"]
    for word in words:
        if word in informal:
            errors["register"] += 1
    
    # --- CONFIDENCE SCORE ---
    total_errors = sum(errors.values())
    errors["confidence_score"] = min(1.0, total_errors / 3.0)
    
    return errors

# Create the Diagnostic Agent
diagnostic_agent = Agent(
    name="diagnostic_agent",
    description="Analyzes student submissions for errors",
    model="gemini-2.0-flash",
    instruction="""
    You are a Diagnostic Agent. Use the analyze_text tool to analyze student English for errors.
    Report findings clearly.
    """,
    tools=[FunctionTool(analyze_text)]
)