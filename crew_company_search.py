
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
def initialize_crew(anthropic_api_key, serper_api_key):

    llm = LLM(
        api_key=anthropic_api_key,
        model="anthropic/claude-3-5"  
    )
    
    resume_tool = FileReadTool(file_path="resume.txt")
    web_search_tool = SerperDevTool(api_key=serper_api_key)
    # Define agents (same as before)
    company_researcher = Agent(
        role="Company Researcher",
        goal="Gather insights about {company} and its industry.",
        backstory="A skilled researcher focused on company analysis.",
        verbose=True,
        llm=LLM(api_key=anthropic_api_key),
    )
    industry_researcher = Agent(
        role="Industry Researcher",
        goal="Analyze trends and insights in the {industry} industry.",
        backstory="An expert in industry analysis.",
        verbose=True,
        llm=LLM(api_key=anthropic_api_key),
    )
    contact_finder = Agent(
        role="Contact Finder",
        goal="Identify relevant contacts at {company}.",
        backstory="A professional networker skilled at finding key personnel.",
        verbose=True,
        llm=LLM(api_key=anthropic_api_key),
    )
    message_crafter = Agent(
        role="Message Crafter",
        goal="Draft personalized emails for outreach.",
        backstory="An expert communicator focused on creating engaging messages.",
        verbose=True,
        llm=LLM(api_key=anthropic_api_key),
    )
    
    # Define tasks with output schemas
    company_research_task = Task(
        description="Research relevant details about {company}.",
        expected_output="A list of key company insights.",
        output_schema=CompanyInsight,
        agent=company_researcher,
    )
    industry_research_task = Task(
        description="Analyze the {industry} industry for trends and opportunities.",
        expected_output="A list of key industry insights.",
        output_schema=IndustryInsight,
        agent=industry_researcher,
    )
    contact_research_task = Task(
        description="Identify 2–3 key contacts for outreach at {company}.",
        expected_output="A list of contacts with names, roles, and emails.",
        output_schema=ContactsOutput,
        agent=contact_finder,
    )
    message_crafting_task = Task(
        description="Draft a personalized email for outreach to {company}.",
        expected_output="A draft email in text format.",
        output_schema=EmailDraft,
        agent=message_crafter,
    )
    
    # Define crew
    crew = Crew(
        agents=[company_researcher, industry_researcher, contact_finder, message_crafter],
        tasks=[company_research_task, industry_research_task, contact_research_task, message_crafting_task],
        process=Process.sequential,
        memory=False,
    )
    return crew



