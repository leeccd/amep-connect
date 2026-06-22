from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# This function will analyze student text for errors
def analyze_text(text: str) -> dict:
    """
    Analyzes student text for common English errors.
    Returns a dictionary with error categories.
    """
    errors = {
        "word_order": 0,
        "spelling": 0,
        "grammar": 0,
        "register": 0,
        "confidence_score": 0.0
    }
    
    # Simple rule-based analysis (will be enhanced with Gemini later)
    words = text.lower().split()
    
    # Word order check: look for common inversion errors
    if "is" in words and any(word in words for word in ["what", "where", "when", "how"]):
        # Check for subject-verb inversion errors
        errors["word_order"] += 1
    
    # Spelling: check for common misspellings (simplified example)
    common_misspellings = {
        "teh": "the",
        "recieve": "receive",
        "definately": "definitely"
    }
    for word in words:
        if word in common_misspellings:
            errors["spelling"] += 1
    
    # Grammar: check for missing articles
    if "the" not in words and "a" not in words and "an" not in words:
        errors["grammar"] += 1
    
    # Register: check for informal language in formal context (simplified)
    informal_words = ["gonna", "wanna", "kinda", "sorta"]
    for word in words:
        if word in informal_words:
            errors["register"] += 1
    
    # Confidence score (higher = more errors found)
    total_errors = sum(errors.values())
    errors["confidence_score"] = min(1.0, total_errors / 10)
    
    return errors

# Create the Diagnostic Agent
diagnostic_agent = Agent(
    name="diagnostic_agent",
    description="Analyzes student submissions for errors in word order, spelling, grammar, and register",
    model="gemini-2.0-flash",
    instruction="""
    You are a Diagnostic Agent for AMEP Connect.
    Your role is to analyze student English submissions and identify errors.
    
    Use the analyze_text tool to categorize errors as:
    - Word Order (WO): Incorrect sentence structure
    - Spelling (Sp): Misspelled words
    - Grammar (Gr): Issues with articles, verb tense, etc.
    - Register (RD): Using informal language in formal contexts
    
    After analysis, provide a brief summary of the error types found.
    """,
    tools=[FunctionTool(analyze_text)]
)