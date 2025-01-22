import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
from pathlib import Path
import PyPDF2
import io
from crew_company_search import initialize_crew
from typing import Dict, Any, List, Optional

# Page configuration
st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="💼",
    layout="wide"
)

# Initialize session state
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'crew_result' not in st.session_state:
    st.session_state.crew_result = None

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: auto;
        padding: 0.5rem 2rem;
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
    }
    .main .block-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .section-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    .contact-card {
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    .email-container {
        background-color: white;
        padding: 1.5rem;
        border: 1px solid #dee2e6;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

def pdf_to_text(uploaded_file) -> str:
    """Convert uploaded PDF to text with error handling."""
    try:
        if not uploaded_file:
            raise ValueError("No file uploaded")
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        
        if not text.strip():
            raise ValueError("No text content found in PDF")
        return text
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def parse_research(text: str) -> Dict[str, List[str]]:
    """Parse research output into sections."""
    sections = {}
    current_section = None
    current_points = []
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if line.endswith(':'):
            if current_section and current_points:
                sections[current_section] = current_points
            current_section = line[:-1]
            current_points = []
        elif line.startswith('- ') or line.startswith('* '):
            current_points.append(line[2:])
        elif current_section:
            current_points.append(line)
    
    if current_section and current_points:
        sections[current_section] = current_points
    
    return sections

def parse_contacts(text: str) -> List[Dict[str, str]]:
    """Parse contact information into structured format."""
    contacts = []
    current_contact = {}
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            if current_contact:
                contacts.append(current_contact)
                current_contact = {}
            continue
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            current_contact[key] = value
    
    if current_contact:
        contacts.append(current_contact)
    
    return contacts

def update_tabs_with_content(result):
    """Update tabs with CrewAI results."""
    tab1, tab2, tab3 = st.tabs(["📊 Research", "👥 Contacts", "✉️ Email"])
    
    try:
        # Debug output to understand the result structure
        st.write("Debug - Result type:", type(result))
        st.write("Debug - Result attributes:", dir(result) if result else "None")
        
        # Initialize outputs
        research_output = None
        contact_output = None
        email_output = None
        
        # Handle CrewOutput object
        if hasattr(result, 'tasks_output') and result.tasks_output:
            tasks = result.tasks_output
            if len(tasks) >= 3:
                research_output = tasks[0].result
                contact_output = tasks[1].result
                email_output = tasks[2].result
        elif hasattr(result, 'raw') and result.raw:
            # If we only have raw output, use it for all tabs
            research_output = contact_output = email_output = result.raw
        
        # Display Research Tab
        with tab1:
            st.subheader("Company & Industry Research")
            if research_output:
                try:
                    sections = parse_research(research_output)
                    for section, points in sections.items():
                        st.markdown(f"### {section}")
                        for point in points:
                            st.markdown(f"• {point}")
                        st.markdown("---")
                except Exception as e:
                    st.error(f"Error parsing research: {str(e)}")
                    st.markdown(research_output)
            else:
                st.warning("No research data available")

        # Display Contacts Tab
        with tab2:
            st.subheader("Key Contacts")
            if contact_output:
                try:
                    contacts = parse_contacts(contact_output)
                    for contact in contacts:
                        with st.expander(f"{contact.get('Contact Name', 'Unknown')} - {contact.get('Role', 'Unknown Role')}"):
                            for key, value in contact.items():
                                if key != 'Contact Name':
                                    st.markdown(f"**{key}:** {value}")
                except Exception as e:
                    st.error(f"Error parsing contacts: {str(e)}")
                    st.markdown(contact_output)
            else:
                st.warning("No contact data available")

        # Display Email Tab
        with tab3:
            st.subheader("Email Draft")
            if email_output:
                try:
                    st.text_area(
                        "Email Content",
                        value=email_output,
                        height=300,
                        key="email_content"
                    )
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("📋 Copy"):
                            st.code(email_output)
                            st.success("Copied to clipboard!")
                except Exception as e:
                    st.error(f"Error displaying email: {str(e)}")
                    st.markdown(email_output)
            else:
                st.warning("No email draft available")

    except Exception as e:
        st.error(f"Error updating content: {str(e)}")
        st.error("Raw result structure:")
        if hasattr(result, 'raw'):
            st.markdown(result.raw)
        else:
            st.write(result)

def main():
    st.title("AI Job Application Assistant 💼")
    
    st.markdown("""
    ### Streamline Your Job Application Process
    Upload your resume and let AI help you with:
    - In-depth company and industry research
    - Identifying key contacts
    - Crafting personalized outreach messages
    """)

    # File upload
    uploaded_file = st.file_uploader(
        "📄 Upload Resume (PDF)",
        type=['pdf'],
        help="Upload your resume in PDF format"
    )

    # Target information
    st.subheader("🎯 Target Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        industry = st.text_input(
            "Industry",
            help="Target industry (e.g., Digital Signage, Software)"
        )
        
        company = st.text_input(
            "Company Name",
            help="Target company name"
        )

    with col2:
        pitching_role = st.text_input(
            "Desired Role",
            help="Position you're applying for"
        )
        
        outreach_purpose = st.selectbox(
            "Outreach Purpose",
            options=["job opportunities", "networking", "internship"],
            help="Select your primary outreach goal"
        )

    # Generate button
    if st.button("🚀 Generate Application Materials", type="primary"):
        if not uploaded_file:
            st.error("⚠️ Please upload your resume first!")
            return
        
        if not all([industry, company, pitching_role]):
            st.error("⚠️ Please fill in all required fields!")
            return
        
        try:
            # Process resume
            resume_text = pdf_to_text(uploaded_file)
            
            # Save resume text to a temporary file in the current working directory
            resume_path = os.path.join(os.getcwd(), "resume.txt")
            with open(resume_path, "w", encoding="utf-8") as f:
                f.write(resume_text)
            
            # Initialize CrewAI with error handling
            with st.spinner("Initializing AI agents..."):
                try:
                    crew_instance = initialize_crew(
                        anthropic_api_key=st.secrets['ANTHROPIC_API_KEY'],
                        serper_api_key=st.secrets['SERPER_API_KEY']
                    )
                except Exception as e:
                    st.error(f"Failed to initialize AI agents: {str(e)}")
                    return
            
            inputs = {
                "industry": industry,
                "outreach_purpose": outreach_purpose,
                "pitching_role": pitching_role,
                "company": company,
                "resume_path": resume_path  # Pass the full path to the resume file
            }
            
            with st.spinner("🔍 Analyzing and generating materials..."):
                try:
                    result = crew_instance.kickoff(inputs=inputs)
                    
                    # Debug output
                    st.write("Debug - Result type:", type(result))
                    st.write("Debug - Result structure:", result)
                    
                    if result is None:
                        st.error("No results generated. The AI agents returned None.")
                        return
                        
                    st.session_state.crew_result = result
                    st.session_state.generation_complete = True
                    
                    update_tabs_with_content(result)
                    st.success("✨ Application materials generated successfully!")
                except Exception as e:
                    st.error(f"Error during generation: {str(e)}")
                    st.error("Please try again or contact support.")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please try again or contact support.")
        finally:
            # Clean up the temporary resume file
            try:
                if os.path.exists(resume_path):
                    os.remove(resume_path)
            except Exception as e:
                st.warning(f"Could not remove temporary file: {str(e)}")

    # Show results or placeholders
    if not st.session_state.generation_complete:
        tab1, tab2, tab3 = st.tabs(["📊 Research", "👥 Contacts", "✉️ Email"])
        with tab1:
            st.info("Company and industry research will appear here.")
        with tab2:
            st.info("Key contacts will be listed here.")
        with tab3:
            st.info("Your personalized email will appear here.")
    elif st.session_state.crew_result:
        update_tabs_with_content(st.session_state.crew_result)

if __name__ == "__main__":
    main()
