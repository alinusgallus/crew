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
        goal="Find relevant hiring managers or team leaders at {company}.",
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
            description="""Research {company} focusing on:
            - Recent developments and news
            - Company culture and values
            - Products or services
            - Growth trajectory
            Return insights as a CompanyResearch object.""",
            agent=company_researcher,
            output_schema=CompanyResearch,
            expected_output="Structured company insights with key findings.",
            context=[
                "Focus on information relevant to job seekers",
                "Look for recent company developments",
                "Identify company culture and values"
            ]
        ),
        
        Task(
            description="""Analyze the {industry} industry focusing on:
            - Current trends and challenges
            - Growth opportunities
            - Required skills and qualifications
            Return insights as an IndustryResearch object.""",
            agent=industry_researcher,
            output_schema=IndustryResearch,
            expected_output="Structured industry analysis with key trends.",
            context=[
                "Focus on recent industry trends",
                "Identify key skills and qualifications",
                "Look for growth areas and opportunities"
            ]
        ),
        
        Task(
            description="""Identify 2-3 relevant contacts at {company} who might be involved in hiring for {pitching_role}.
            Include their roles and any available contact information.
            Return as a ContactResearch object.""",
            agent=contact_finder,
            output_schema=ContactResearch,
            expected_output="List of relevant contacts with their roles.",
            context=[
                "Focus on finding hiring managers",
                "Look for team leads in relevant departments",
                "Identify decision makers for the target role"
            ]
        ),
        
        Task(
            description="""Using the company research and contact information, craft a personalized outreach email:
            - Mention specific company details that interest you
            - Reference your relevant experience
            - Keep it concise and professional
            Return as an EmailDraft object.""",
            agent=message_crafter,
            output_schema=EmailDraft,
            expected_output="Personalized email draft for company outreach.",
            context=[
                "Use insights from company research",
                "Highlight relevant experience",
                "Keep the tone professional but personal"
            ]
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
