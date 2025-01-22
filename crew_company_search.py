import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import List, Optional
from pydantic import BaseModel
from crewai import Agent, Crew, Task, Process, LLM
from crewai_tools import SerperDevTool, FileReadTool
import litellm

# Enable verbose logging for LiteLLM
litellm.set_verbose = True

# Pydantic models for structured output
class CompanyResearch(BaseModel):
    company_name: str
    key_insights: List[str]

class IndustryResearch(BaseModel):
    industry_name: str
    key_insights: List[str]

class Contact(BaseModel):
    name: str
    role: str
    email: Optional[str] = None

class ContactResearch(BaseModel):
    contacts: List[Contact]

class EmailDraft(BaseModel):
    email_draft: str

def initialize_crew(anthropic_api_key: str, serper_api_key: str) -> Crew:
    """
    Initialize a CrewAI instance with configured agents and tasks.
    """
    # Initialize LLM
    llm = LLM(
        api_key=anthropic_api_key,
        model='anthropic/claude-3-5-sonnet-20240620'
    )
    
    # Initialize tools
    resume_tool = FileReadTool(file_path="resume.txt")
    web_search_tool = SerperDevTool(api_key=serper_api_key)
    
    # Define agents
    company_researcher = Agent(
        role="Company Researcher",
        goal="Research and analyze {company} to identify key information and recent developments.",
        backstory="""Expert business researcher skilled at finding and analyzing company information.
        You focus on recent developments, company culture, and business strategies.""",
        verbose=True,
        llm=llm,
        tools=[web_search_tool, resume_tool]
    )
    
    industry_researcher = Agent(
        role="Industry Researcher",
        goal="Analyze the {industry} industry landscape and identify key trends.",
        backstory="""Industry analysis expert who identifies market trends, challenges, and opportunities.
        You provide context about industry dynamics and competitive landscapes.""",
        verbose=True,
        llm=llm,
        tools=[web_search_tool]
    )
    
    contact_finder = Agent(
        role="Contact Finder",
        goal="Find relevant contacts at {company}.",
        backstory="""Expert at identifying key personnel within organizations.
        You focus on finding decision-makers relevant to the job seeker's interests.""",
        verbose=True,
        llm=llm,
        tools=[web_search_tool]
    )
    
    message_crafter = Agent(
        role="Message Crafter",
        goal="Create a compelling outreach message for {company} contacts.",
        backstory="""Professional communications expert who crafts personalized outreach messages.
        You create engaging emails that highlight relevant experience and show genuine interest.""",
        verbose=True,
        llm=llm,
        tools=[resume_tool]
    )
    
    # Define tasks with output schemas
    tasks = [
        Task(
            description="""Research {company} and return as a JSON object with:
            - company_name: the company name
            - key_insights: a list of key findings about recent developments, culture, products, and growth""",
            agent=company_researcher,
            output_json=True,
            output_schema=CompanyResearch
        ),
        
        Task(
            description="""Analyze the {industry} industry and return as a JSON object with:
            - industry_name: the industry name
            - key_insights: a list of trends, challenges, and opportunities""",
            agent=industry_researcher,
            output_json=True,
            output_schema=IndustryResearch
        ),
        
        Task(
            description="""Find 2-3 contacts at {company} and return as a JSON object with:
            - contacts: a list of contact objects, each with:
              - name: the contact's name
              - role: their role at the company
              - email: their email if available""",
            agent=contact_finder,
            output_json=True,
            output_schema=ContactResearch
        ),
        
        Task(
            description="""Create an email draft and return as a JSON object with:
            - email_draft: the complete email text""",
            agent=message_crafter,
            output_json=True,
            output_schema=EmailDraft
        )
    ]
    
    # Create crew
    crew = Crew(
        agents=[company_researcher, industry_researcher, contact_finder, message_crafter],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=False
    )
    
    return crew

if __name__ == "__main__":
    # Example usage
    api_keys = {
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "serper": os.getenv("SERPER_API_KEY")
    }
    
    crew_instance = initialize_crew(
        anthropic_api_key=api_keys["anthropic"],
        serper_api_key=api_keys["serper"]
    )
    
    # Example inputs
    inputs = {
        "company": "Example Corp",
        "industry": "Technology",
        "pitching_role": "Software Engineer",
        "outreach_purpose": "job opportunities"
    }
    
    # Run the crew
    result = crew_instance.kickoff(inputs=inputs)
    print(result)
