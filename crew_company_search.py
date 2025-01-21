
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
import os
import crewai
import crewai_tools
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from crewai import Agent, Crew, Task, Process, LLM
from crewai_tools import SerperDevTool, FileReadTool
import litellm  

# Enable verbose logging for LiteLLM
litellm.set_verbose = True

# Set your API key

os.environ['ANTHROPIC_API_KEY'] = st.secrets['ANTHROPIC_API_KEY']
os.environ["SERPER_API_KEY"] = st.secrets['SERPER_API_KEY']

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY is not set. Please check your Streamlit secrets or environment configuration.")

# Initialize the LLM
llm = LLM(
    api_key=anthropic_api_key,  # Explicitly pass the API key as a named argument
    model="anthropic/claude-3-5-sonnet-20240620",  # Specify the model name
)
resume_tool = FileReadTool(file_path="resume.txt")
web_search_tool = SerperDevTool()

class CompanyInsight(BaseModel):
    name: str
    industry_focus: str
    key_challenges: str
    recent_news: str

class Contact(BaseModel):
    name: str
    role: str
    email: Optional[str] = None  # Email is optional

class CompanyData(BaseModel):
    company_insights: Dict[str, CompanyInsight]
    contacts: Dict[str, List[Contact]]

 # Setup agents
company_researcher = Agent(
    role= "Company Researcher",
    goal= "Gather insigths about {company} and its industry to qualify it as a potential lead for {outreach_purpose}",
    backstory= "A seasoned researcher specializing in gathering detailed information about companies.",
    tools=[web_search_tool],
    verbose =True,
    llm = llm,
    max_retry_limit=2,
    max_rpm=20,
)
industry_researcher = Agent(
    role= "Industry Researcher",
    goal= "Gather insigths about the following industry: {industry}, focusing on {outreach_purpose} context",
    backstory= "A seasoned market researcher specializing in gathering detailed information about companies and their industries.",
    tools=[web_search_tool],
    verbose =True,
    llm = llm,
    max_retry_limit=2,
    max_rpm=20,
)

contact_finder = Agent(
    role="Contact Finder",
    goal="Identify suitable contacts within {company} for {outreach_purpose}.",
    backstory="An expert networker skilled at identifying key personnel within organizations.",
    tools=[web_search_tool],
    verbose =True,
    llm = llm,
    max_retry_limit=2,
    max_rpm=20,
)

message_crafter = Agent(
    role="Message Crafter",
    goal=(
        "Write 2 compelling and personalized 300 words emails for {outreach_purpose} at {company}, "
        "highlighting the user's suitability as a {pitching_role}. Use the resume details dynamically."
    ),
    backstory="A creative communicator skilled at crafting engaging messages using available data.",
    tools=[resume_tool,web_search_tool],
    verbose =True,
    llm = llm,
    max_retry_limit=2,
    max_rpm=20,
 )

 # Setup Tasks
company_research_task = Task(
    description="Research relevant details about {company} in order to assess opportunites for {outreach_purpose}.",
    expected_output="A list of 10 key insights about {company} and their suitability for {outreach_purpose}.",
    agent=company_researcher,
)
industry_research_task = Task(
    description="Research relevant details about {industry} in order to assess opportunites for {outreach_purpose}.",
    expected_output="A list of 10 key insights about {industry} and their suitability for {outreach_purpose}.",
    agent=industry_researcher,
)

contact_research_task = Task(
    description="Identify 2–3 key contacts for outreach at {company}.",
    expected_output="A dictionary of contacts with names, roles, and contact details.",
    agent=contact_finder,
)

message_crafting_task = Task(
    description=(
        "Craft a personalized email for {outreach_purpose} in the based on your knowledge of the {industry} industry and insights on {company}, "
        "contact details, and dynamically retrieved resume details."
    ),
    expected_output="A polished,concise,2 paragraph long, ready-to-send personalized email highlighting suitability as a {pitching_role}.",
    agent=message_crafter,
)


# Define the Crew
crew = Crew(
    agents=[company_researcher,industry_researcher, contact_finder, message_crafter],
    tasks=[company_research_task, industry_research_task, contact_research_task, message_crafting_task],
    process=Process.sequential,
    memory=False,
)

# Inputs for the Crew
inputs = {
    "industry": "Digital Signage",  # Example: Specify the industry
    "outreach_purpose": "job opportunities",  # Example: Specify the purpose
    "pitching_role": "Senior Product Manager",  # Example: Specify the role you're pitching
    "company": "Cenareo", # Company to research
}
# Step 7: Run the Crew and Validate Data with Pydantic
try:
    raw_result = crew.kickoff(inputs=inputs)
except Exception as e:
    st.error(f"An error occurred while executing the crew: {e}")
    raise


st.write("### Raw Results")
st.json(raw_result)

