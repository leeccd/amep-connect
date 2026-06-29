"""
AMEP Connect - Streamlit UI
Interactive interface for the multi-agent system
"""

import streamlit as st
import sys
import os
import re
import datetime

def log(message):
    """Print a timestamped log message"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Add parent directory to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents
from amep_connect.diagnostic_agent import analyze_text
from amep_connect.scaffolding_agent import generate_scaffolding
from amep_connect.admin_agent import track_progress
from mcp_server.server import mcp_server

# Security functions (defined here to avoid import issues)
def is_safe_text(text: str) -> bool:
    """Quick check if text is safe to process."""
    patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # email
        r'\b\d{10}\b',  # phone
        r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Road|Rd|Avenue|Ave)\b',  # address
        r'\b(?:[A-Z]{1,2}\d{6,8})\b',  # Australian visa
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True

def mask_pii(text: str) -> str:
    """Quick function to mask PII in text."""
    # Mask emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', text)
    # Mask phone numbers
    text = re.sub(r'\b\d{10}\b', '[REDACTED]', text)
    # Mask addresses (simplified)
    text = re.sub(r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Road|Rd|Avenue|Ave)\b', '[REDACTED]', text)
    # Mask Australian visa numbers
    text = re.sub(r'\b(?:[A-Z]{1,2}\d{6,8})\b', '[REDACTED]', text)
    return text

# Page configuration
st.set_page_config(
    page_title="AMEP Connect",
    page_icon="🎓",
    layout="wide"
)

# Title
st.title("🎓 AMEP Connect: Cert III Nexus")
st.subheader("Multi-Agent Autonomous Scaffolding for Adult Language Learners")

# Sidebar with information
with st.sidebar:
    st.header("About AMEP Connect")
    st.markdown("""
    **Agents for Good** - Advancing Education
    
    This system uses three specialized AI agents to help adult migrants 
    improve their English language skills:
    
    - **🔍 Diagnostic Agent**: Analyzes errors in student submissions
    - **📚 Scaffolding Agent**: Provides personalized exercises
    - **📊 Admin Portal Agent**: Tracks progress and competency
    
    Built with Google ADK, MCP, and Streamlit.
    """)
    
    st.divider()
    
    st.header("CSWE III Standards")
    standards = mcp_server.get_standards()
    for skill, items in list(standards.items())[:2]:
        with st.expander(f"{skill.upper()}"):
            for item in items[:2]:
                st.write(f"- {item}")
    
    st.divider()
    
    st.caption("⚠️ No student data is stored. All processing is temporary.")

# Main interface
st.header("✍️ Student Submission")

# Input area
student_text = st.text_area(
    "Enter the student's English text:",
    height=150,
    placeholder="Example: I going to the shop yestaday and I buyed milk..."
)

student_id = st.text_input(
    "Student ID (optional):",
    placeholder="e.g., student_001"
)

# Process button
if st.button("🚀 Analyze & Generate", type="primary"):
    if not student_text:
        st.warning("Please enter some text to analyze.")
    else:
        with st.spinner("Processing with AMEP Connect agents..."):
              # --- ADD THESE PRINT STATEMENTS ---
            print("\n" + "="*50)
            print("📝 Processing student submission...")
            print(f"   Text: {student_text}")
            print("="*50)
            # ------------------------------------
            # Step 1: Security Check
            if not is_safe_text(student_text):
                print("⚠️ PII detected - masking...")
                st.warning("⚠️ Sensitive information detected. Masking PII...")
                masked_text = mask_pii(student_text)
                st.info(f"Text after PII masking: {masked_text}")
                text_to_process = masked_text
            else:
                print("✅ No PII detected")
                text_to_process = student_text
            
            # Step 2: Diagnostic Agent
            st.subheader("🔍 Step 1: Diagnostic Analysis")
            print("🔍 Diagnostic Agent: Analyzing text...")
            errors = analyze_text(text_to_process)
            
            # Display error breakdown
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Word Order", errors.get("word_order", 0))
            with col2:
                st.metric("Spelling", errors.get("spelling", 0))
            with col3:
                st.metric("Grammar", errors.get("grammar", 0))
            with col4:
                st.metric("Register", errors.get("register", 0))
            
            st.caption(f"Confidence Score: {errors.get('confidence_score', 0):.2f}")
            
            # Step 3: Scaffolding Agent
            st.subheader("📚 Step 2: Personalized Interventions")
            interventions = generate_scaffolding(errors, text_to_process)
            
            for category, items in interventions.items():
                if items and category != "confidence_score":
                    with st.expander(f"📖 {category.upper()} Exercises"):
                        for item in items:
                            if item.startswith("🔹") or item.startswith("🌟") or item.startswith("📝"):
                                st.write(item)
                            else:
                                st.write(f"  {item}")
            
            # Step 4: Admin Portal Agent
            if student_id:
                st.subheader("📊 Step 3: Progress Tracking")
                report = track_progress(student_id, errors)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Errors", report["total_errors"])
                with col2:
                    st.metric("CSWE Level", report["cswe_level"])
                with col3:
                    improvement_areas = len(report["areas_needing_improvement"])
                    st.metric("Areas to Improve", improvement_areas)
                
                if report["areas_needing_improvement"]:
                    st.write("**Areas needing improvement:**")
                    for area in report["areas_needing_improvement"]:
                        st.write(f"- {area}")
            
            # Step 5: MCP Context (optional)
            with st.expander("📖 View MCP Curriculum Context"):
                st.json(mcp_server.get_standards())

# Footer
st.divider()
st.caption("AMEP Connect - Built with Google ADK, MCP, and Streamlit for the Kaggle AI Agents Capstone")