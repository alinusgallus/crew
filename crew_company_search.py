import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import List, Optional, Dict, Any
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, FileReadTool
import json

def load_resume() -> str:
    """Safely load resume content with error handling."""
    try:
        if not os.path.exists("resume.txt"):
            raise FileNotFoundError("Resume file not found")
        with open("resume.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading resume: {str(e)}")

def create_tools(serper_api_key: str) -> Dict[str, Any]:
    """Create and validate tools with error handling."""
    try:
        search_tool = SerperDevTool(
            serper_api_key=serper_api_key,
            retry_on_fail=True
        )
        
        file_tool = FileReadTool(
            file_path="resume.txt",
            retry_on_fail=True
        )
        
        return {
            "search": search_tool,
            "resume": file_tool
        }
    except Exception as e:
        raise Exception(f"Error creating tools: {str(e)}")

def initialize_crew(
    anthropic_api_key: str, 
    serper_api_key: str,
    company: str = "",
    industry: str = "",
    pitching_role: str = "",
    country: str = "",
    outreach_purpose: str = ""
) -> Crew:
    """
    Initialize CrewAI with robust error handling and validated configuration.
    """
    try:
        # Validate API keys
        if not anthropic_api_key or not serper_api_key:
            raise ValueError("Missing required API keys")
        
        # Set required environment variables
        llm = LLM(api_key = anthropic_api_key, model="anthropic/claude-3-sonnet-20240229")

        
        # Create tools
        tools = create_tools(serper_api_key)
        
        # Validate resume exists
        load_resume()
        
        # Create researcher agent
        researcher = Agent(
            role="Research Specialist",
            goal=f"""Analyze companies and industries to provide comprehensive insights 
            for job applications and professional outreach.""",
            backstory="""You are an expert in corporate research and industry analysis 
            with years of experience helping job seekers understand potential employers.""",
            tools=[tools["search"]],
            verbose=True,
            allow_delegation=False,
            llm=llm,
            llm_config={
                "temperature": 0.2,
                "retry_delay": 10,
                "max_retries": 3,
            },
        )
        
        # Create contact finder agent
        contact_finder = Agent(
            role="Contact Specialist",
            goal="""Find relevant hiring managers and team leads at target companies.""",
            backstory="""You are an expert in identifying key decision-makers and 
            hiring managers within organizations.""",
            tools=[tools["search"]],
            verbose=True,
            allow_delegation=False,
            llm=LLM(api_key = anthropic_api_key, model="anthropic/claude-3-haiku-20240307"),
            llm_config={
                "temperature": 0.2,
                "retry_delay": 10,
                "max_retries": 3,
            },
        )
        
        # Create email writer agent
        writer = Agent(
            role="Communications Expert",
            goal="Craft compelling and personalized outreach messages",
            backstory="""Professional writer specializing in job search communications. 
            You excel at creating engaging, personalized messages that highlight relevant 
            experience and generate responses.""",
            tools=[tools["resume"]],
            verbose=True,
            allow_delegation=False,
            llm=llm,
            llm_config={
                "temperature": 0.6,
                "retry_delay": 10,
                "max_retries": 3,
            },
        )
        
        # Research task
        research = Task(
            description=f"""Analyze {company} and the {industry} industry.
                Consider the specific context of {country} market.
                Provide information in the following format:

                Company Overview:
                - Key facts about the company
                - Recent developments
                - Company culture and values
                - Local presence in {country}

                Industry Analysis:
                - Current trends in {country}
                - Growth opportunities
                - Key challenges
                - Local market dynamics
                - Industry-specific qualifications
                - Local requirements/certifications
                
                Provide ONLY these sections, with bullet points for each item.""",
            agent=researcher,
            expected_output="A structured analysis with Company Overview and Industry Analysis sections."
        )
        
        # Contact task
        contacts = Task(
            description=f"""Find 2-3 relevant contacts at {company} for the {pitching_role} position.
                Focus on contacts in {country} or with responsibility for {country}.
                Format each contact as:

                Contact Name: [Full Name]
                Role: [Current Role]
                Location: [Country/Office]
                Background: [Brief background]
                LinkedIn: [LinkedIn profile URL if available]
                Email: [Email if available]

                Separate each contact with a blank line.
                Make sure to include LinkedIn profiles when possible as they are important for outreach.
                Focus on hiring managers and team leads.""",
            agent=contact_finder,
            expected_output="A list of 2-3 formatted contact profiles for relevant hiring managers or team leads."
        )
        
        # Email task
        email = Task(
            description=f"""Write a personalized outreach email for {company}.
                Consider the local business culture in {country}.
                
                Use this exact structure:
                ---
                Subject: [Clear subject line]

                Dear [Contact's Name],

                [Opening with specific company detail]

                [Paragraph about relevant experience]

                [Closing with clear call to action]

                Best regards,
                [Your name]
                ---
                
                Keep the total length under 200 words.
                Use information from the research and resume.""",
            agent=writer,
            expected_output="A formatted email following the specified structure.",
            context=[research, contacts]
        )
        
        # Create crew
        crew = Crew(
            agents=[researcher, contact_finder, writer],
            tasks=[research, contacts, email],
            process=Process.hierarchical,
            manager_llm=llm,
            verbose=True
        )
        
        return crew
        
    except Exception as e:
        raise Exception(f"Error initializing crew: {str(e)}")

if __name__ == "__main__":
    try:
        # Test configuration
        api_keys = {
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "serper": os.getenv("SERPER_API_KEY")
        }
        
        if not all(api_keys.values()):
            raise ValueError("Missing required API keys in environment variables")
        
        crew = initialize_crew(
            anthropic_api_key=api_keys["anthropic"],
            serper_api_key=api_keys["serper"]
        )
        
        # Test inputs
        inputs = {
            "company": "Example Corp",
            "industry": "Technology",
            "pitching_role": "Software Engineer"
        }
        
        # Run crew
        result = crew.kickoff(inputs=inputs)
        
        # Just print the results directly
        print("\nResults:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error in test run: {str(e)}")
