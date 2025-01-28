from pydantic import BaseModel, Field, validator
from typing import List
from enum import Enum

class CompanyStage(str, Enum):
    STARTUP = "startup"
    ESTABLISHED = "established"
    MULTINATIONAL = "multinational"

class WorkModel(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    OFFICE = "office"

class CompanyDetails(BaseModel):
    employees: str = Field(..., description="Employee count range")
    offices_count: str = Field(..., description="Number of office locations")
    company_stage: CompanyStage
    financial_status: str
    core_business: List[str]
    geographical_presence: List[str]
    organizational_structure: str

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "employees": "1,000-5,000 employees globally",
                "offices_count": "15 offices across 3 continents",
                "company_stage": "established",
                "financial_status": "Publicly traded, steady growth, $500M annual revenue",
                "core_business": [
                    "Enterprise Software Solutions",
                    "Cloud Infrastructure Services",
                    "Digital Transformation Consulting"
                ],
                "geographical_presence": [
                    "Headquarters in London",
                    "Major hubs in New York, Singapore",
                    "Development centers in Eastern Europe"
                ],
                "organizational_structure": "Matrix structure with regional and functional reporting lines"
            }
        }

class PositionContext(BaseModel):
    department_overview: str
    reporting_structure: str
    growth_plans: List[str]
    key_projects: List[str]
    required_qualifications: List[str]
    similar_roles: List[str]

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "department_overview": "Marketing team of 25 people, responsible for global brand strategy",
                "reporting_structure": "Reports to Senior Marketing Director with 2 direct reports",
                "growth_plans": [
                    "Expanding digital marketing team by 40% this year",
                    "Opening new regional marketing hubs",
                    "Increasing marketing budget by 25%"
                ],
                "key_projects": [
                    "Global brand refresh initiative",
                    "Marketing automation implementation",
                    "New product launch campaigns"
                ],
                "required_qualifications": [
                    "5+ years in B2B marketing",
                    "Experience with marketing automation tools",
                    "Team leadership background"
                ],
                "similar_roles": [
                    "Content Marketing Manager",
                    "Digital Marketing Lead",
                    "Marketing Operations Manager"
                ]
            }
        }

class WorkEnvironment(BaseModel):
    company_values: List[str]
    culture_description: str
    development_programs: List[str]
    benefits_overview: List[str]
    leadership_style: str
    employee_reviews: List[str]
    work_model: WorkModel

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "company_values": [
                    "Innovation First",
                    "Customer Obsession",
                    "Diversity and Inclusion"
                ],
                "culture_description": "Fast-paced, collaborative environment with focus on work-life balance",
                "development_programs": [
                    "Leadership development tracks",
                    "Professional certification support",
                    "Mentorship program"
                ],
                "benefits_overview": [
                    "Comprehensive health coverage",
                    "Flexible working hours",
                    "Learning and development budget"
                ],
                "leadership_style": "Transparent and collaborative with open-door policy",
                "employee_reviews": [
                    "Strong emphasis on professional growth",
                    "Supportive management team",
                    "Good work-life balance"
                ],
                "work_model": "hybrid"
            }
        }

class MarketPosition(BaseModel):
    industry_ranking: str
    key_competitors: List[str]
    differentiators: List[str]
    major_partnerships: List[str]
    recent_achievements: List[str]
    industry_challenges: List[str]

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "industry_ranking": "Top 5 in enterprise software segment",
                "key_competitors": [
                    "Competitor A - Market leader",
                    "Competitor B - Innovation focused",
                    "Competitor C - Regional strong player"
                ],
                "differentiators": [
                    "Proprietary AI technology",
                    "Strong customer service focus",
                    "Rapid implementation methodology"
                ],
                "major_partnerships": [
                    "Strategic alliance with Microsoft",
                    "AWS Advanced Partner",
                    "Industry consortium leader"
                ],
                "recent_achievements": [
                    "Industry Innovation Award 2024",
                    "Fastest growing in sector",
                    "Top employer recognition"
                ],
                "industry_challenges": [
                    "Talent shortage in key areas",
                    "Rapid technological change",
                    "Increasing regulatory requirements"
                ]
            }
        }

class ProfessionalGrowth(BaseModel):
    skill_requirements: List[str]
    career_paths: List[str]
    certifications: List[str]
    salary_ranges: str
    professional_associations: List[str]
    industry_outlook: List[str]

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "skill_requirements": [
                    "Project management",
                    "Technical architecture",
                    "Team leadership"
                ],
                "career_paths": [
                    "Individual Contributor to Team Lead",
                    "Technical Expert to Architecture",
                    "Management Track Options"
                ],
                "certifications": [
                    "PMP",
                    "Industry-specific certs",
                    "Technical certifications"
                ],
                "salary_ranges": "Entry: $70-90k, Mid: $90-120k, Senior: $120-180k, Lead: $150k+",
                "professional_associations": [
                    "Industry Association A",
                    "Professional Network B",
                    "Technical Community C"
                ],
                "industry_outlook": [
                    "15% growth projected",
                    "Increasing demand for specialists",
                    "Emerging technology adoption"
                ]
            }
        }

class LocalMarket(BaseModel):
    regional_status: str
    business_environment: str
    local_competitors: List[str]
    employment_regulations: List[str]
    business_culture: List[str]
    required_permits: List[str]

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "regional_status": "Major tech hub with growing opportunities",
                "business_environment": "Supportive ecosystem with government incentives",
                "local_competitors": [
                    "Local Leader A",
                    "Regional Player B",
                    "Emerging Startup C"
                ],
                "employment_regulations": [
                    "Standard work visa requirements",
                    "Local labor laws compliance",
                    "Industry-specific regulations"
                ],
                "business_culture": [
                    "Collaborative work environment",
                    "Work-life balance focused",
                    "Innovation-driven culture"
                ],
                "required_permits": [
                    "Work permit requirements",
                    "Professional certifications",
                    "Industry-specific licenses"
                ]
            }
        }

class CompanyAnalysis(BaseModel):
    company_details: CompanyDetails
    position_context: PositionContext
    work_environment: WorkEnvironment

    class Config:
        extra = "forbid"

class IndustryAnalysis(BaseModel):
    market_position: MarketPosition
    professional_growth: ProfessionalGrowth
    local_market: LocalMarket

    class Config:
        extra = "forbid"

class ResearchOutput(BaseModel):
    company_analysis: CompanyAnalysis
    industry_analysis: IndustryAnalysis

    class Config:
        extra = "forbid"
        validate_assignment = True

        @validator('*', pre=True)
        def check_completeness(cls, v):
            """Ensure all required information is meaningful"""
            if isinstance(v, str) and len(v.strip()) < 10:
                raise ValueError("Field content must be meaningful and complete")
            return v
        
        