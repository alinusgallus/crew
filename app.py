import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import streamlit as st
import os
from pathlib import Path
import PyPDF2
import io
import json
from crew_company_search import initialize_crew

# Page configuration
st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="💼",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: auto;
        padding: 0.5rem 2rem;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    .stMarkdown {
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

def pdf_to_text(uploaded_file):
    """Convert uploaded PDF to text"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

def render_tabs_with_placeholders():
    """Render initial tabs with placeholders"""
    tab1, tab2, tab3 = st.tabs(["📊 Company Research", "👥 Contacts", "✉️ Email Draft"])
    
    with tab1:
        st.subheader("Company Insights")
        st.info("Company research and industry insights will appear here after generation.")
        
    with tab2:
        st.subheader("Key Contacts")
        st.info("Relevant company contacts will be listed here after generation.")
        
    with tab3:
        st.subheader("Email Draft")
        st.info("Your personalized email draft will appear here after generation.")

def update_tabs_with_content(result_dict):
    """Update tabs with actual content"""
    tab1, tab2, tab3 = st.tabs(["📊 Company Research", "👥 Contacts", "✉️ Email Draft"])
    
    with tab1:
        st.subheader("Company Insights")
        if "company_research" in result_dict:
            st.markdown(result_dict["company_research"])
        if "industry_insights" in result_dict:
            st.markdown("### Industry Analysis")
            st.markdown(result_dict["industry_insights"])

    with tab2:
        st.subheader("Key Contacts")
        if "contacts" in result_dict:
            contacts = result_dict["contacts"]
            if isinstance(contacts, list):
                for contact in contacts:
                    with st.expander(contact.split(":")[0] if ":" in contact else contact):
                        st.markdown(contact)
            elif isinstance(contacts, str):
                st.markdown(contacts)

    with tab3:
        st.subheader("Email Draft")
        if "email_draft" in result_dict:
            email_content = result_dict["email_draft"]
            if email_content.startswith("Subject:"):
                subject, body = email_content.split("\n", 1)
                st.markdown("**" + subject.strip() + "**")
                email_content = body.strip()
            
            email_area = st.text_area(
                "Email Content",
                value=email_content,
                height=300,
                key="email_content"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("📋 Copy to Clipboard"):
                    st.code(email_content)
                    st.success("Email copied!")

def main():
    st.title("AI Job Application Assistant 💼")
    
    st.markdown("""
    ### About This Application
    This AI-powered tool helps you streamline your job application process by:
    - Researching target companies and their industry
    - Finding relevant contacts within the organization
    - Crafting personalized outreach messages
    - Using your resume to highlight relevant experience
    """)

    # File upload and input form
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF format)", type=['pdf'])

    st.subheader("🎯 Target Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        industry = st.text_input(
            "Industry",
            value="Digital Signage",
            help="Enter the industry you're targeting"
        )
        
        company = st.text_input(
            "Company Name",
            value="Cenareo",
            help="Enter the name of the company"
        )

    with col2:
        pitching_role = st.text_input(
            "Desired Role",
            value="Product Manager",
            help="Enter the position you're applying for"
        )
        
        outreach_purpose = st.selectbox(
            "Outreach Purpose",
            options=["job opportunities", "networking", "internship"],
            help="Select the purpose of your outreach"
        )

    # Generate button in a column layout
    col1, col2 = st.columns([2, 1])
    with col1:
        generate_button = st.button("Generate Application 🚀")

    # Always render tabs with placeholders
    if 'generation_complete' not in st.session_state:
        render_tabs_with_placeholders()

    if generate_button:
        if not uploaded_file:
            st.error("Please upload your resume before proceeding!")
            return
        
        if not all([industry, company, pitching_role]):
            st.error("Please fill in all required fields!")
            return
        
        # Process the PDF resume
        resume_text = pdf_to_text(uploaded_file)
        if resume_text:
            resume_path = Path("resume.txt")
            resume_path.write_text(resume_text)
            
            try:
                crew_instance = initialize_crew(
                    anthropic_api_key=st.secrets['ANTHROPIC_API_KEY'],
                    serper_api_key=st.secrets['SERPER_API_KEY']
                )
                
                inputs = {
                    "industry": industry,
                    "outreach_purpose": outreach_purpose,
                    "pitching_role": pitching_role,
                    "company": company
                }
                
                with st.spinner("🔍 Researching and crafting your application..."):
                    raw_result = crew_instance.kickoff(inputs=inputs)
                    
                    if raw_result:
                        st.success("✨ Application materials generated successfully!")
                        
                        # Convert string result to dict if needed
                        if isinstance(raw_result, str):
                            try:
                                result_dict = json.loads(raw_result)
                            except:
                                result_dict = {"raw": raw_result}
                        else:
                            result_dict = raw_result

                        # Update tabs with actual content
                        st.session_state.generation_complete = True
                        update_tabs_with_content(result_dict)
                    else:
                        st.error("No results were generated. Please try again.")
                        
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error("Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    main()
