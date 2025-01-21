from crew_company_search import initialize_crew
import streamlit as st
import os
from pathlib import Path
import PyPDF2
import io

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
    
    crew = initialize_crew(anthropic_api_key,serper_api_key)
    
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
            
            # Prepare inputs for the crew
            inputs = {
                "industry": industry,
                "outreach_purpose": outreach_purpose,
                "pitching_role": pitching_role,
                "company": company
            }
            
            # Show processing status
            with st.spinner("🔍 Researching and crafting your application..."):
                try:
                    # Execute crew
                    raw_result = crew.kickoff(inputs=inputs)
                    
                    # Display results in organized tabs
                    st.success("✨ Application materials generated successfully!")
                    
                    tabs = st.tabs(["📊 Company Research", "👥 Contacts", "✉️ Email Draft"])
                    
                    with tabs[0]:
                        st.subheader("Company Insights")
                        if "company_insights" in raw_result:
                            with st.container():
                                st.markdown("### 🏢 Company Overview")
                                st.write(raw_result["company_insights"].get("industry_focus", ""))
                                
                                st.markdown("### 📰 Recent News")
                                st.write(raw_result["company_insights"].get("recent_news", ""))
                                
                                st.markdown("### 🎯 Key Challenges")
                                st.write(raw_result["company_insights"].get("key_challenges", ""))
                        else:
                            st.info("No company insights available")
                    
                    with tabs[1]:
                        st.subheader("Key Contacts")
                        if "contacts" in raw_result:
                            for contact in raw_result["contacts"]:
                                with st.expander(f"{contact.get('name', 'Unknown')} - {contact.get('role', 'Role not specified')}"):
                                    st.write(f"**Role:** {contact.get('role', 'N/A')}")
                                    if contact.get('email'):
                                        st.write(f"**Email:** {contact['email']}")
                        else:
                            st.info("No contact information available")
                    
                    with tabs[2]:
                        st.subheader("Personalized Email Draft")
                        if "email_draft" in raw_result:
                            email_content = raw_result["email_draft"]
                            st.text_area("Email Content", email_content, height=300)
                            
                            # Copy button for email
                            if st.button("📋 Copy Email to Clipboard"):
                                st.code(email_content)  # Shows in a copyable format
                                st.success("Email copied to clipboard!")
                        else:
                            st.info("No email draft available")
                    
                    # Save results button
                    if st.button("💾 Save Results"):
                        # Implementation for saving results
                        st.success("Results saved successfully!")
                        
                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")
                    st.error("Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    main()
