import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from typing import List, Optional, Dict, Any
from crewai import Agent, Task, Crew, Process
import LLM
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

def initialize_crew(anthropic_api_key: str, serper_api_key: str) -> Crew:
    """
    Initialize CrewAI with robust error handling and validated configuration.
    """
    try:
        # Validate API keys
        if not anthropic_api_key or not serper_api_key:
            raise ValueError("Missing required API keys")
        
        # Set required environment variables
        llm = LLM(anthropic_api_key = anthropic_api_key, model="anthropic/claude-3-sonnet-20240229")

        
        # Create tools
        tools = create_tools(serper_api_key)
        
        # Validate resume exists
        load_resume()
        
        # Create researcher agent
        researcher = Agent(
            role="Research Specialist",
            goal="Gather comprehensive information about the target company and industry",
            backstory="""Expert business researcher with years of experience analyzing 
            companies and industries. You excel at finding key information about company 
            culture, recent developments, and industry trends.""",
            tools=[tools["search"]],
            verbose=True,
            allow_delegation=False
            llm=llm
        )
        
        # Create contact finder agent
        contact_finder = Agent(
            role="Contact Specialist",
            goal="Identify appropriate hiring managers and decision makers",
            backstory="""Expert at finding relevant contacts within organizations. 
            You focus on identifying hiring managers and team leaders who would be 
            involved in the hiring process.""",
            tools=[tools["search"]],
            verbose=True,
            allow_delegation=False
            llm=llm
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
            allow_delegation=False
            llm=llm
        )
        
        # Research task
        research = Task(
            description="""Analyze {company} and the {industry} industry.
            Provide information in the following format:

            Company Overview:
            - Key facts about the company
            - Recent developments
            - Company culture and values

            Industry Analysis:
            - Current trends
            - Growth opportunities
            - Key challenges

            Required Skills:
            - Technical skills
            - Soft skills
            - Industry-specific qualifications
            
            Provide ONLY these sections, with bullet points for each item.""",
            agent=researcher,
            expected_output="A structured analysis with Company Overview, Industry Analysis, and Required Skills sections."
        )
        
        # Contact task
        contacts = Task(
            description="""Find 2-3 relevant contacts at {company} for the {pitching_role} position.
            Format each contact as:

            Contact Name: [Full Name]
            Role: [Current Role]
            Background: [Brief background]
            Email: [Email if available]

            Separate each contact with a blank line.
            Focus on hiring managers and team leads.""",
            agent=contact_finder,
            expected_output="A list of 2-3 formatted contact profiles for relevant hiring managers or team leads."
        )
        
        # Email task
        email = Task(
            description="""Write a personalized outreach email for {company}.
            
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
            expected_output="A formatted email following the specified structure."
        )
        
        # Create crew
        crew = Crew(
            agents=[researcher, contact_finder, writer],
            tasks=[research, contacts, email],
            process=Process.sequential,
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
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error in test run: {str(e)}")
