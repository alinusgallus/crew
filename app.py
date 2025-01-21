import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)


import streamlit as st
import os
from pathlib import Path
import PyPDF2
import io
from crew_company_search import initialize_crew

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
    # Set your API key

    os.environ['ANTHROPIC_API_KEY'] = st.secrets['ANTHROPIC_API_KEY']
    os.environ["SERPER_API_KEY"] = st.secrets['SERPER_API_KEY']

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set. Please check your Streamlit secrets or environment configuration.")
    
    serper_api_key = os.getenv("SERPER_API_KEY")
    
    crew_instance = initialize_crew(anthropic_api_key,serper_api_key)
    
    # Page title and configuration
    st.set_page_config(
        page_title="AI Job Application Assistant",
        page_icon="💼",
        layout="wide"
    )

    st.title("AI Job Application Assistant 💼")

    # Description Block
    st.markdown("""
    ### About This Application
    This AI-powered tool helps you streamline your job application process by:
    - Researching target companies and their industry
    - Finding relevant contacts within the organization
    - Crafting personalized outreach messages
    - Using your resume to highlight relevant experience
    
    Simply upload your resume and fill in the details below to get started!
    """)

    # Create a form for user inputs
    with st.form("job_application_form"):
        # Resume Upload Section
        st.subheader("📄 Upload Your Resume")
        uploaded_file = st.file_uploader("Upload your resume (PDF format only)", type=['pdf'])
        
        # Input Fields Section
        st.subheader("🎯 Target Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            industry = st.text_input(
                "Industry",
                help="Enter the industry you're targeting (e.g., Digital Signage, Software, Healthcare)"
            )
            
            company = st.text_input(
                "Company Name",
                help="Enter the name of the company you're interested in"
            )

        with col2:
            pitching_role = st.text_input(
                "Desired Role",
                help="Enter the position you're applying for (e.g., Senior Product Manager)"
            )
            
            outreach_purpose = st.selectbox(
                "Outreach Purpose",
                options=["job opportunities", "networking", "internship"],
                help="Select the main purpose of your outreach"
            )

        # Submit button
        submit_button = st.form_submit_button("Generate Application 🚀")

    # Handle form submission
    if submit_button:
    try:
        # ... (your existing code until crew execution)
        
        with st.spinner("🔍 Researching and crafting your application..."):
            raw_result = crew_instance.kickoff(inputs=inputs)
            
            # Create three columns for better organization
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📊 Company Research")
                try:
                    if isinstance(raw_result, dict):
                        st.info(raw_result.get('company_research', 'No company research available'))
                    else:
                        st.text(str(raw_result))
                except Exception as e:
                    st.error(f"Error displaying company research: {e}")

            with col2:
                st.markdown("### 🎯 Industry Insights")
                try:
                    if isinstance(raw_result, dict):
                        st.info(raw_result.get('industry_insights', 'No industry insights available'))
                    else:
                        st.text(str(raw_result))
                except Exception as e:
                    st.error(f"Error displaying industry insights: {e}")

            with col3:
                st.markdown("### 👥 Key Contacts")
                try:
                    if isinstance(raw_result, dict) and 'contacts' in raw_result:
                        for contact in raw_result['contacts']:
                            st.write(f"- {contact}")
                    else:
                        st.info("No contact information available")
                except Exception as e:
                    st.error(f"Error displaying contacts: {e}")

            # Email draft section
            st.markdown("### ✉️ Generated Email")
            try:
                if isinstance(raw_result, dict) and 'email_draft' in raw_result:
                    email_content = raw_result['email_draft']
                    st.text_area("Email Content", email_content, height=200)
                    if st.button("📋 Copy to Clipboard"):
                        st.code(email_content)
                        st.success("Email copied to clipboard!")
                else:
                    st.warning("No email draft available in the expected format")
                    st.text(str(raw_result))
            except Exception as e:
                st.error(f"Error displaying email draft: {e}")

            # Debug information in expander
            with st.expander("🔍 Debug Information"):
                st.write("Raw Result Type:", type(raw_result))
                st.write("Raw Result Content:", raw_result)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error("Please try again or contact support if the issue persists.")
        
if __name__ == "__main__":
    main()
