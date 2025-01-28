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
from models import (
    ResearchOutput, CompanyAnalysis, IndustryAnalysis,
    CompanyDetails, PositionContext, WorkEnvironment,
    MarketPosition, ProfessionalGrowth, LocalMarket,
    CompanyStage, WorkModel
)

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
                
                Provide a comprehensive analysis following this exact structure:

                Company Analysis:
                1. Company Details:
                   - Employee count range
                   - Number of office locations
                   - Company stage (startup/established/multinational)
                   - Financial status
                   - Core business areas
                   - Geographical presence
                   - Organizational structure

                2. Position Context:
                   - Department overview
                   - Reporting structure
                   - Growth plans
                   - Key projects
                   - Required qualifications
                   - Similar roles

                3. Work Environment:
                   - Company values
                   - Culture description
                   - Development programs
                   - Benefits overview
                   - Leadership style
                   - Employee reviews
                   - Work model (remote/hybrid/office)

                Industry Analysis:
                1. Market Position:
                   - Industry ranking
                   - Key competitors
                   - Differentiators
                   - Major partnerships
                   - Recent achievements
                   - Industry challenges

                2. Professional Growth:
                   - Skill requirements
                   - Career paths
                   - Relevant certifications
                   - Salary ranges
                   - Professional associations
                   - Industry outlook

                3. Local Market ({country}):
                   - Regional status
                   - Business environment
                   - Local competitors
                   - Employment regulations
                   - Business culture
                   - Required permits

                Format the response as structured data that can be parsed into the ResearchOutput model.
                Ensure all fields are meaningful and complete.""",
            agent=researcher,
            expected_output=ResearchOutput(
                company_analysis=CompanyAnalysis(
                    company_details=CompanyDetails(
                        employees="",
                        offices_count="",
                        company_stage=CompanyStage.ESTABLISHED,
                        financial_status="",
                        core_business=[],
                        geographical_presence=[],
                        organizational_structure=""
                    ),
                    position_context=PositionContext(
                        department_overview="",
                        reporting_structure="",
                        growth_plans=[],
                        key_projects=[],
                        required_qualifications=[],
                        similar_roles=[]
                    ),
                    work_environment=WorkEnvironment(
                        company_values=[],
                        culture_description="",
                        development_programs=[],
                        benefits_overview=[],
                        leadership_style="",
                        employee_reviews=[],
                        work_model=WorkModel.HYBRID
                    )
                ),
                industry_analysis=IndustryAnalysis(
                    market_position=MarketPosition(
                        industry_ranking="",
                        key_competitors=[],
                        differentiators=[],
                        major_partnerships=[],
                        recent_achievements=[],
                        industry_challenges=[]
                    ),
                    professional_growth=ProfessionalGrowth(
                        skill_requirements=[],
                        career_paths=[],
                        certifications=[],
                        salary_ranges="",
                        professional_associations=[],
                        industry_outlook=[]
                    ),
                    local_market=LocalMarket(
                        regional_status="",
                        business_environment="",
                        local_competitors=[],
                        employment_regulations=[],
                        business_culture=[],
                        required_permits=[]
                    )
                )
            ).dict()
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

def parse_research_output(result: str) -> Dict[str, Any]:
    """Parse and validate the research output using the ResearchOutput model."""
    try:
        # Convert the string result to a dictionary
        if isinstance(result, str):
            result_dict = json.loads(result)
        else:
            result_dict = result
            
        # Validate using the ResearchOutput model
        research_output = ResearchOutput(**result_dict)
        return research_output.dict()
    except Exception as e:
        raise Exception(f"Error parsing research output: {str(e)}")

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
        
        # Parse and validate the results
        parsed_results = parse_research_output(result)
        
        # Print the validated results
        print("\nValidated Results:")
        print(json.dumps(parsed_results, indent=2))
        
    except Exception as e:
        print(f"Error in test run: {str(e)}")
