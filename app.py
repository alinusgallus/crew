import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

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
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def pdf_to_text(uploaded_file) -> str:
    """Convert uploaded PDF to text with caching."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        if not text.strip():
            raise ValueError("No text content found in PDF")
        return text
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def update_tabs_with_content(result):
    """Update tabs with CrewAI results."""
    tab1, tab2, tab3 = st.tabs(["📊 Research", "👥 Contacts", "✉️ Email"])
    
    with tab1:
        st.subheader("Company & Industry Insights")
        
        # Display company research
        try:
            company_insights = result.tasks[0].output
            st.markdown("### Company Insights")
            for insight in company_insights.key_insights:
                st.markdown(f"• {insight}")
        except (AttributeError, IndexError) as e:
            st.info("Company research is being processed...")
            
        # Display industry research
        try:
            industry_insights = result.tasks[1].output
            st.markdown("### Industry Insights")
            for insight in industry_insights.key_insights:
                st.markdown(f"• {insight}")
        except (AttributeError, IndexError) as e:
            st.info("Industry research is being processed...")

    with tab2:
        st.subheader("Key Contacts")
        try:
            contacts = result.tasks[2].output.contacts
            for contact in contacts:
                with st.expander(f"{contact.name} - {contact.role}"):
                    st.markdown(f"**Role:** {contact.role}")
                    if contact.email:
                        st.markdown(f"**Email:** {contact.email}")
        except (AttributeError, IndexError) as e:
            st.info("Contact information is being processed...")

    with tab3:
        st.subheader("Email Draft")
        try:
            email_draft = result.tasks[3].output.email_draft
            st.text_area(
                "Email Content",
                value=email_draft,
                height=300,
                key="email_content"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📋 Copy"):
                    st.code(email_draft)
                    st.success("Copied to clipboard!")
        except (AttributeError, IndexError) as e:
            st.info("Email draft is being processed...")

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

    # Input form
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
            resume_path = Path("resume.txt")
            resume_path.write_text(resume_text)
            
            # Initialize CrewAI
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
            
            with st.spinner("🔍 Analyzing and generating materials..."):
                result = crew_instance.kickoff(inputs=inputs)
                
                if result:
                    st.session_state.crew_result = result
                    st.session_state.generation_complete = True
                    
                    # Update UI with results
                    update_tabs_with_content(result)
                    st.success("✨ Application materials generated successfully!")
                else:
                    st.error("No results generated. Please try again.")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please try again or contact support.")

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
