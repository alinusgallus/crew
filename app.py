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

def update_tabs_with_content(result, tabs):
    """Update tabs with CrewAI results."""
    tab1, tab2, tab3 = tabs  # Unpack the tabs
    
    try:
        # Convert CrewOutput to dictionary format
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else {}
        
        # Initialize outputs
        research_output = None
        contact_output = None
        email_output = None
        
        # Try to get outputs from tasks_output
        if 'tasks_output' in result_dict and result_dict['tasks_output']:
            tasks = result_dict['tasks_output']
            if len(tasks) >= 3:
                # Access the raw field from each task
                research_output = tasks[0]['raw']
                contact_output = tasks[1]['raw']
                email_output = tasks[2]['raw']
        
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
                    # Remove the "Based on my research" prefix if present
                    if contact_output.startswith("Based on my research"):
                        contact_output = contact_output.split("\n\n", 1)[1]
                    
                    contacts = parse_contacts(contact_output)
                    for contact in contacts:
                        with st.expander(f"{contact.get('Contact Name', 'Unknown')} - {contact.get('Role', 'Unknown Role')}"):
                            # Display fields in specific order
                            display_order = ['Role', 'Location', 'Background', 'LinkedIn', 'Email']
                            
                            for field in display_order:
                                if field == 'LinkedIn' and field in contact:
                                    st.markdown(f"**LinkedIn:** [{contact[field]}]({contact[field]})")
                                elif field == 'Email':
                                    # Always show email field, even if not found
                                    email_value = contact.get(field, 'Not found')
                                    st.markdown(f"**Email:** {email_value}")
                                elif field in contact:
                                    st.markdown(f"**{field}:** {contact[field]}")
                            
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
        try:
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            st.markdown(raw_output)
        except:
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

    # Add note about privacy and performance
    st.info("""
    ℹ️ **Important Notes:**
    - This is a prototype application and may run slower than a production version
    - No user data or resumes are stored - all information is processed in memory and immediately deleted
    - Each generation takes about 2-3 minutes to complete
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
        
        # Add country selection
        country = st.selectbox(
            "Country",
            options=[
                "France", "United States", "United Kingdom", "Germany", 
                "Singapore", "Australia", "Canada", "Japan", "Netherlands",
                "Switzerland", "Other"
            ],
            help="Select the country where the position is located"
        )
        
        outreach_purpose = st.selectbox(
            "Outreach Purpose",
            options=["job opportunities", "networking", "internship"],
            help="Select your primary outreach goal"
        )

    # Generate button and results
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
                        serper_api_key=st.secrets['SERPER_API_KEY'],
                        company=company,
                        industry=industry,
                        pitching_role=pitching_role,
                        country=country,
                        outreach_purpose=outreach_purpose
                    )
                except Exception as e:
                    st.error(f"Failed to initialize AI agents: {str(e)}")
                    return
            
            inputs = {
                "industry": industry,
                "outreach_purpose": outreach_purpose,
                "pitching_role": pitching_role,
                "company": company,
                "country": country,  # Add country to inputs
                "resume_path": resume_path  # Pass the full path to the resume file
            }
            
            with st.spinner("🔍 Analyzing and generating materials..."):
                try:
                    result = crew_instance.kickoff(inputs=inputs)
                    
                    if result is None:
                        st.error("No results generated. The AI agents returned None.")
                        return
                        
                    st.session_state.crew_result = result
                    st.session_state.generation_complete = True
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

    # Show results or placeholders - AFTER the generate button
    tabs = st.tabs(["📊 Research", "👥 Contacts", "✉️ Email"])
    
    if not st.session_state.generation_complete:
        with tabs[0]:
            st.info("Company and industry research will appear here.")
        with tabs[1]:
            st.info("Key contacts will be listed here.")
        with tabs[2]:
            st.info("Your personalized email will appear here.")
    elif st.session_state.crew_result:
        update_tabs_with_content(st.session_state.crew_result, tabs)

if __name__ == "__main__":
    main()
