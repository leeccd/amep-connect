from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name="search_assistant",
    description="An agent that answers questions using web searches",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Answer questions using Google Search when needed.",
    tools=[google_search]
)