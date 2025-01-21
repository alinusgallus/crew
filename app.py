import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import streamlit as st
import os
from pathlib import Path
import PyPDF2
import io
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
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
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

    if st.button("Generate Application 🚀"):
        if not uploaded_file:
            st.error("Please upload your resume before proceeding!")
            return
        
        if not all([industry, company, pitching_role]):
            st.error("Please fill in all required fields!")
            return
        
        # Process the PDF resume
        resume_text = pdf_to_text(uploaded_file)
        if resume_text:
            # Save resume text to a file
            resume_path = Path("resume.txt")
            resume_path.write_text(resume_text)
            
            try:
                # Initialize crew with secrets
                crew_instance = initialize_crew(
                    anthropic_api_key=st.secrets['ANTHROPIC_API_KEY'],
                    serper_api_key=st.secrets['SERPER_API_KEY']
                )
                
                # Prepare inputs
                inputs = {
                    "industry": industry,
                    "outreach_purpose": outreach_purpose,
                    "pitching_role": pitching_role,
                    "company": company
                }
                
                # Execute crew with progress indication
                with st.spinner("🔍 Researching and crafting your application..."):
                    raw_result = crew_instance.kickoff(inputs=inputs)
                    
                    if raw_result:
                        st.success("✨ Application materials generated successfully!")
                        
                        # Display results in tabs
                        tab1, tab2, tab3 = st.tabs(["📊 Company Research", 
                                                   "👥 Contacts", 
                                                   "✉️ Email Draft"])
                        
                        with tab1:
                            st.subheader("Company Insights")
                            if isinstance(raw_result, dict):
                                if "company_research" in raw_result:
                                    st.write(raw_result["company_research"])
                                else:
                                    st.write(raw_result)
                            else:
                                st.write(raw_result)

                        with tab2:
                            st.subheader("Identified Contacts")
                            if isinstance(raw_result, dict) and "contacts" in raw_result:
                                for contact in raw_result["contacts"]:
                                    with st.expander(f"{contact.get('name', 'Contact')}"):
                                        st.write(f"Role: {contact.get('role', 'N/A')}")
                                        st.write(f"Email: {contact.get('email', 'N/A')}")
                            else:
                                st.info("No structured contact information available")

                        with tab3:
                            st.subheader("Generated Email")
                            if isinstance(raw_result, dict) and "email_draft" in raw_result:
                                email_content = raw_result["email_draft"]
                            else:
                                email_content = str(raw_result)
                                
                            st.text_area("Email Content", email_content, height=300)
                            if st.button("📋 Copy Email"):
                                st.code(email_content)
                                st.success("Email copied to clipboard!")

                        # Debug information
                        with st.expander("🔍 Debug Information"):
                            st.write("Raw Result Type:", type(raw_result))
                            st.write("Raw Result:", raw_result)
                    else:
                        st.error("No results were generated. Please try again.")
                        
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error("Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    main()
