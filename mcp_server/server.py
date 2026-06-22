"""
MCP Server for AMEP Connect
Provides curriculum data and context to agents
"""

import json
from typing import Dict, List, Optional

# CSWE III Curriculum Standards (simplified)
CSWE_III_STANDARDS = {
    "speaking": [
        "Participate in simple conversations on familiar topics",
        "Give and respond to simple instructions",
        "Express opinions and feelings on familiar topics"
    ],
    "listening": [
        "Understand main points in short conversations",
        "Follow simple instructions",
        "Recognize common vocabulary in workplace contexts"
    ],
    "reading": [
        "Read and understand simple workplace documents",
        "Understand short personal letters and emails",
        "Read and follow simple written instructions"
    ],
    "writing": [
        "Write short personal emails and letters",
        "Complete simple forms and applications",
        "Write simple paragraphs on familiar topics"
    ]
}

# Sample workplace texts (for MCP context)
WORKPLACE_TEXTS = {
    "tenancy_application": """
    TENANCY APPLICATION FORM
    Property Address: 123 Main Street, Sydney
    Applicant Name: _____________
    Current Address: _____________
    Employment Status: _____________
    Annual Income: $_____________
    References: Please provide two professional references.
    """,
    "beach_safety": """
    BEACH SAFETY RULES
    1. Always swim between the red and yellow flags.
    2. Never swim alone or at night.
    3. Be aware of rip currents and strong waves.
    4. Follow instructions from lifeguards.
    5. Keep children within arm's reach.
    """,
    "workplace_email": """
    SUBJECT: Meeting Reminder
    Dear Team,
    Please remember our weekly meeting is at 2:00 PM on Friday in Conference Room B.
    Agenda:
    1. Project updates
    2. Budget review
    3. Next steps
    Bring your progress reports.
    Kind regards,
    Manager
    """
}

# Grading rubrics (for Admin Portal Agent)
GRADING_RUBRICS = {
    "cswe_iii": {
        "description": "Functional English - can participate in workplace and community settings",
        "required_skills": ["speaking", "listening", "reading", "writing"],
        "minimum_proficiency": "Can complete tasks independently with minimal support"
    }
}

class MCPServer:
    """
    Simple MCP Server implementation for AMEP Connect.
    Provides curriculum standards, workplace texts, and grading rubrics.
    """
    
    def __init__(self):
        self.standards = CSWE_III_STANDARDS
        self.workplace_texts = WORKPLACE_TEXTS
        self.rubrics = GRADING_RUBRICS
    
    def get_standards(self, skill: Optional[str] = None) -> Dict:
        """Get CSWE III standards. If skill specified, return only that skill."""
        if skill and skill in self.standards:
            return {skill: self.standards[skill]}
        return self.standards
    
    def get_workplace_text(self, text_name: str) -> Optional[str]:
        """Get a workplace text by name."""
        return self.workplace_texts.get(text_name)
    
    def get_all_workplace_texts(self) -> Dict:
        """Get all workplace texts."""
        return self.workplace_texts
    
    def get_rubric(self, level: str) -> Optional[Dict]:
        """Get grading rubric for a specific CSWE level."""
        return self.rubrics.get(level)
    
    def find_standard_by_keyword(self, keyword: str) -> List[str]:
        """Search standards for a keyword."""
        results = []
        for skill, standards in self.standards.items():
            for standard in standards:
                if keyword.lower() in standard.lower():
                    results.append(f"[{skill}] {standard}")
        return results
    
    def get_context_for_agent(self, agent_type: str) -> Dict:
        """Get relevant context for a specific agent type."""
        context = {
            "diagnostic": {
                "standards": self.get_standards(),
                "rubrics": self.get_rubric("cswe_iii")
            },
            "scaffolding": {
                "workplace_texts": self.get_all_workplace_texts(),
                "standards": self.get_standards()
            },
            "admin": {
                "rubrics": self.rubrics,
                "standards": self.get_standards()
            }
        }
        return context.get(agent_type, {})
    
    def to_json(self) -> str:
        """Serialize the server data to JSON."""
        return json.dumps({
            "standards": self.standards,
            "workplace_texts": self.workplace_texts,
            "rubrics": self.rubrics
        }, indent=2)

# Create a singleton instance
mcp_server = MCPServer()

# Test function
def test_mcp_server():
    """Test the MCP Server functionality."""
    print("=" * 50)
    print("MCP SERVER - TEST")
    print("=" * 50)
    
    print("\n📚 CSWE III Standards:")
    for skill, standards in mcp_server.get_standards().items():
        print(f"  {skill.upper()}:")
        for standard in standards:
            print(f"    - {standard}")
    
    print("\n📄 Workplace Texts Available:")
    for name in mcp_server.get_all_workplace_texts().keys():
        print(f"  - {name}")
    
    print("\n🔍 Search for 'instructions':")
    results = mcp_server.find_standard_by_keyword("instructions")
    for result in results:
        print(f"  - {result}")
    
    print("\n🎯 Context for Diagnostic Agent:")
    context = mcp_server.get_context_for_agent("diagnostic")
    print(f"  Standards: {len(context.get('standards', {}))} skills available")
    print(f"  Rubrics: {list(context.get('rubrics', {}).keys())}")
    
    print("\n✅ MCP Server test completed!")

if __name__ == "__main__":
    test_mcp_server()