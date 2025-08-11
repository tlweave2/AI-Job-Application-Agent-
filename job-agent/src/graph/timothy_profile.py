#!/usr/bin/env python3
"""
Timothy Weaver Profile Integration
Personalized job application automation using Tim's background and experience
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TimothyProfile:
    """Timothy Weaver's complete professional profile"""
    
    # Personal Information
    first_name: str = "Timothy"
    last_name: str = "Weaver"
    preferred_name: str = "Tim"
    email: str = "tlweave2@asu.edu"
    phone: str = "209-261-5308"
    website: str = "www.timothylweaver.com"
    linkedin: str = "linkedin.com/in/timweaversoftware"
    location: str = "Escalon, California, US"
    
    # Education
    current_degree: str = "Master of Computer Science"
    current_school: str = "Arizona State University"
    graduation_date: str = "May 2025"
    gpa: str = "3.83"
    academic_standing: str = "Dean's List"
    
    # Professional Experience
    current_title: str = "Software Engineering Student"
    years_programming: str = "4+ years"
    primary_languages: List[str] = None
    frameworks: List[str] = None
    databases: List[str] = None
    
    # Work Authorization
    work_authorization: str = "US Citizen"
    security_clearance: str = "None"
    
    # Preferences
    willing_to_relocate: str = "Yes"
    remote_work_preference: str = "Open to remote, hybrid, or on-site"
    start_date: str = "June 2025"
    salary_expectation: str = "Market rate for entry-level SDE"
    
    def __post_init__(self):
        if self.primary_languages is None:
            self.primary_languages = ["Java", "JavaScript", "Python", "C++", "SQL"]
        if self.frameworks is None:
            self.frameworks = ["Spring Boot", "React", "Node.js"]
        if self.databases is None:
            self.databases = ["PostgreSQL", "MySQL", "MongoDB"]

@dataclass
class TimothyExperience:
    """Timothy's detailed work and project experience"""
    
    # Current Project - VidlyAI
    current_project: str = "VidlyAI.Com - AI Video Generation Platform"
    current_role: str = "Full-Stack Developer & Architect"
    current_duration: str = "December 2024 - Present"
    current_description: str = """Designed and developed a complete AI-powered video generation platform from concept to production. 
Built scalable RESTful API backend with Spring Boot, responsive React frontend with mobile-first design, 
PostgreSQL database for efficient video and user data management, server-side video processing with FFmpeg integration, 
and AI content generation using Gemini API."""
    
    # Academic Project - Field Day
    academic_project: str = "Field Day Project - Animal Differentiation System"
    academic_role: str = "Team Developer"
    academic_duration: str = "June 2024 - June 2025"
    academic_description: str = """Capstone project developing animal differentiation system. 
Developed core functionality for animal differentiation system, implemented critical bug fixes improving system stability and performance, 
collaborated using Git for version control, applied Agile methodologies for project management and delivery."""
    
    # Business Experience
    business_title: str = "Business Owner & Operator"
    business_company: str = "Strokers Motorcycle Service"
    business_duration: str = "2003-2020"
    business_description: str = """Founded and managed successful motorcycle service business for 18 years. 
Implemented digital inventory and customer relationship management systems, managed team of technicians and support staff, 
developed training programs maintaining high customer satisfaction, coordinated with vendors, customers, and team members."""
    
    # Clinical Engineering
    clinical_title: str = "Clinical Engineer / Department Head"
    clinical_company: str = "Stanford University Hospital / Mt. Zion Hospital"
    clinical_duration: str = "1995-2002"
    clinical_description: str = """Maintained critical medical equipment ensuring optimal performance. 
Served as Department Head at Mt. Zion Hospital, San Francisco. Implemented preventive maintenance programs, 
managed equipment budgets and vendor relationships, collaborated with medical staff to troubleshoot complex system issues."""
    
    # Military Service
    military_branch: str = "United States Army"
    military_duration: str = "1990-1994"
    military_location: str = "Walter Reed Medical Hospital"
    military_achievements: str = "Two Army Achievement Medals for meritorious service"

@dataclass
class TimothyResponses:
    """Pre-crafted responses for common job application questions"""
    
    # Why are you interested in this position/company?
    motivation_template: str = """I am excited about this opportunity because it aligns perfectly with my passion for software development and my goal to apply my technical skills in a collaborative, innovative environment. 

With my unique background combining 18+ years of business leadership, military discipline, and recent intensive focus on full-stack development, I bring both technical competency and strong professional maturity to this role.

Through my current VidlyAI project, I've demonstrated my ability to architect and build complete applications from concept to production, working with modern technologies like Spring Boot, React, and AI integration. My academic performance (3.83 GPA, Dean's List) and hands-on project experience have prepared me well for the challenges of professional software development.

I'm particularly drawn to [COMPANY] because of [SPECIFIC_REASON - will be customized based on company research]. I'm eager to contribute to your team while continuing to learn from experienced engineers and growing my technical expertise."""

    # Tell us about yourself
    about_me: str = """I'm a dedicated software engineering student at Arizona State University, graduating in May 2025 with a 3.83 GPA and consistent Dean's List recognition. I'm currently pursuing my Master's in Computer Science starting August 2025.

My journey to software engineering is unique - I'm a military veteran with 18+ years of successful business ownership and clinical engineering experience before transitioning to software development. This diverse background has given me strong leadership skills, systematic problem-solving abilities, and the discipline to tackle complex technical challenges.

Currently, I'm the architect and lead developer for VidlyAI.Com, a full-stack AI video generation platform built with Spring Boot, React, PostgreSQL, and FFmpeg integration. This project showcases my ability to work with modern technologies and deliver production-ready applications.

I'm passionate about continuous learning, whether it's mastering new frameworks, contributing to open source projects, or exploring emerging technologies like AI and machine learning. I'm excited to bring my combination of technical skills, professional maturity, and fresh perspective to a collaborative development team."""

    # Describe your technical experience
    technical_experience: str = """My technical journey began during my Software Engineering program at ASU, where I developed proficiency in Java, C++, JavaScript, Python, and SQL through comprehensive coursework in data structures, algorithms, object-oriented programming, and database management.

My flagship project, VidlyAI.Com, demonstrates my full-stack capabilities:
- Backend: Spring Boot RESTful API with PostgreSQL database design and management
- Frontend: React application with responsive, mobile-first design
- Integration: FFmpeg for server-side video processing and Gemini API for AI content generation
- Architecture: Scalable system design handling user authentication, video processing workflows, and data management

Through my Field Day capstone project, I've gained experience with team development using Git version control and Agile methodologies. I've implemented critical bug fixes and core functionality improvements that enhanced system stability and performance.

My approach to development emphasizes clean, maintainable code, thorough testing, and user-focused design. I'm comfortable working across the full technology stack and am always eager to learn new tools and frameworks that can improve development efficiency and application quality."""

    # Greatest strength
    greatest_strength: str = """My greatest strength is my ability to combine systematic problem-solving with strong leadership and communication skills, developed through my diverse professional background.

Having successfully managed a business for 18 years and led technical teams in clinical engineering, I bring a unique perspective to software development. I approach technical challenges methodically, breaking down complex problems into manageable components while keeping the bigger picture in mind.

This strength was evident in my VidlyAI project, where I had to architect an entire platform from scratch, integrating multiple technologies (Spring Boot, React, PostgreSQL, FFmpeg, AI APIs) while ensuring scalability and maintainability. My business background helped me focus on user experience and practical functionality, while my engineering experience ensured robust, well-tested implementation.

Additionally, my military service instilled strong discipline and attention to detail, which translates into writing clean, well-documented code and following best practices. I'm comfortable taking ownership of projects while also collaborating effectively in team environments."""

    # Why are you transitioning to software engineering?
    career_transition: str = """My transition to software engineering represents the natural evolution of my career-long passion for technology and problem-solving.

Throughout my diverse career - from clinical engineering maintaining complex medical equipment, to running a successful business with digital inventory systems, to military service with advanced technical systems - I've consistently been drawn to the technology aspects of every role.

When I decided to pursue formal education in software engineering, I discovered that programming combines everything I love: logical problem-solving, creative design, continuous learning, and the ability to build solutions that make a real impact. The immediate feedback loop in development and the constant evolution of the field energize me.

My VidlyAI project confirmed this passion - I genuinely enjoy the process of architecting systems, writing clean code, debugging complex issues, and seeing ideas come to life through technology. The 18+ years of business and leadership experience haven't been abandoned; instead, they provide valuable context for understanding user needs, project management, and delivering practical solutions.

This isn't just a career change for me - it's the culmination of a lifelong interest in technology, now backed by formal education, hands-on experience, and the professional maturity to contribute meaningfully to development teams."""

class TimothyProfileProcessor:
    """Process Timothy's profile for job application automation"""
    
    def __init__(self):
        self.profile = TimothyProfile()
        self.experience = TimothyExperience()
        self.responses = TimothyResponses()
    
    def get_basic_info_mapping(self) -> Dict[str, str]:
        """Get basic field mappings for simple forms"""
        return {
            "personal.first_name": self.profile.first_name,
            "personal.last_name": self.profile.last_name,
            "personal.full_name": f"{self.profile.first_name} {self.profile.last_name}",
            "personal.preferred_name": self.profile.preferred_name,
            "personal.email": self.profile.email,
            "personal.phone": self.profile.phone,
            "personal.website": self.profile.website,
            "personal.linkedin": self.profile.linkedin,
            "personal.location": self.profile.location,
            "personal.city": "Escalon",
            "personal.state": "California",
            "personal.country": "United States",
            "personal.zip_code": "95320",
            
            # Education
            "education.school": self.profile.current_school,
            "education.degree": self.profile.current_degree,
            "education.graduation_date": self.profile.graduation_date,
            "education.gpa": self.profile.gpa,
            "education.major": "Computer Science",
            "education.level": "Master's",
            
            # Experience
            "experience.current_title": self.profile.current_title,
            "experience.years_programming": self.profile.years_programming,
            "experience.years_experience": "4+ years",
            "experience.current_company": "Arizona State University",
            
            # Work Authorization
            "authorization.work_status": self.profile.work_authorization,
            "authorization.visa_required": "No",
            "authorization.security_clearance": self.profile.security_clearance,
            
            # Preferences
            "preferences.willing_to_relocate": self.profile.willing_to_relocate,
            "preferences.remote_work": self.profile.remote_work_preference,
            "preferences.start_date": self.profile.start_date,
            "preferences.salary_expectation": self.profile.salary_expectation,
            
            # Technical Skills (as comma-separated strings)
            "skills.programming_languages": ", ".join(self.profile.primary_languages),
            "skills.frameworks": ", ".join(self.profile.frameworks),
            "skills.databases": ", ".join(self.profile.databases),
            "skills.primary_language": "Java",
            "skills.years_java": "4+ years",
            "skills.years_javascript": "3+ years",
            "skills.years_python": "2+ years"
        }
    
    def get_rag_context(self) -> Dict[str, Any]:
        """Get rich context for RAG content generation"""
        return {
            "personal": asdict(self.profile),
            "experience": asdict(self.experience),
            "responses": asdict(self.responses),
            "technical_skills": {
                "languages": self.profile.primary_languages,
                "frameworks": self.profile.frameworks,
                "databases": self.profile.databases,
                "specialties": ["Full-stack development", "AI integration", "Database design", "System architecture"]
            },
            "projects": {
                "vidlyai": {
                    "name": "VidlyAI.Com",
                    "role": "Full-Stack Developer & Architect",
                    "duration": "December 2024 - Present",
                    "technologies": ["Spring Boot", "React", "PostgreSQL", "FFmpeg", "Gemini AI"],
                    "achievements": [
                        "Architected complete AI video generation platform",
                        "Built scalable RESTful API backend",
                        "Created responsive React frontend",
                        "Integrated AI content generation",
                        "Implemented video processing pipeline"
                    ]
                },
                "field_day": {
                    "name": "Field Day - Animal Differentiation System",
                    "role": "Team Developer",
                    "duration": "June 2024 - June 2025",
                    "technologies": ["Java", "Git", "Agile methodologies"],
                    "achievements": [
                        "Developed core system functionality",
                        "Implemented critical bug fixes",
                        "Improved system stability and performance",
                        "Collaborated in team environment"
                    ]
                }
            },
            "unique_background": {
                "military_service": "US Army (1990-1994) - Walter Reed Medical Hospital",
                "business_ownership": "18+ years running Strokers Motorcycle Service",
                "clinical_engineering": "7+ years at Stanford University Hospital",
                "leadership_experience": "Managed teams, budgets, and complex technical projects",
                "customer_service": "Extensive client relationship management experience"
            },
            "career_goals": {
                "immediate": "Entry-level Software Development Engineer position",
                "short_term": "Develop expertise in full-stack development and AI integration",
                "long_term": "Advance to senior software engineer with focus on innovative AI applications"
            }
        }
    
    def generate_custom_response(self, question_type: str, question: str, company_context: Dict[str, Any] = None) -> str:
        """Generate customized responses based on question type and company context"""
        
        company_name = company_context.get("name", "[COMPANY]") if company_context else "[COMPANY]"
        
        if "motivation" in question_type.lower() or "why" in question.lower():
            response = self.responses.motivation_template
            if company_context and "values" in company_context:
                # Customize based on company values
                response = response.replace("[SPECIFIC_REASON]", 
                    f"your commitment to {company_context['values'][0]} and the opportunity to work on {company_context.get('focus', 'innovative technology solutions')}")
            return response.replace("[COMPANY]", company_name)
        
        elif "about yourself" in question.lower() or "tell us about" in question.lower():
            return self.responses.about_me
        
        elif "technical" in question.lower() or "experience" in question.lower():
            return self.responses.technical_experience
        
        elif "strength" in question.lower():
            return self.responses.greatest_strength
        
        elif "transition" in question.lower() or "career change" in question.lower():
            return self.responses.career_transition
        
        else:
            # Generic response based on available context
            return f"""Based on my experience as a software engineering student at ASU with a 3.83 GPA and hands-on full-stack development experience through my VidlyAI project, I believe I can contribute effectively to {company_name}. 

My unique background combining military service, 18+ years of business leadership, and technical expertise in Java, Spring Boot, React, and AI integration provides me with both the technical skills and professional maturity to excel in this role.

I'm particularly excited about the opportunity to apply my systematic problem-solving approach and collaborative mindset to help {company_name} achieve its technical goals while continuing to grow my expertise in software development."""

# Integration with the field classifier
class TimothyEnhancedClassifier:
    """Enhanced classifier that incorporates Timothy's profile"""
    
    def __init__(self, base_classifier, timothy_processor=None):
        self.base_classifier = base_classifier
        self.timothy = timothy_processor or TimothyProfileProcessor()
        self.field_mappings = self.timothy.get_basic_info_mapping()
        self.rag_context = self.timothy.get_rag_context()
    
    async def classify_field_with_timothy_context(self, element, page_context):
        """Classify field with Timothy's profile context"""
        
        # Add Timothy's context to page context
        enhanced_context = {
            **page_context,
            "user_profile": self.rag_context,
            "available_mappings": list(self.field_mappings.keys()),
            "applicant_name": "Timothy Weaver",
            "applicant_background": "Software Engineering student with business and military experience"
        }
        
        # Get base classification
        classification = await self.base_classifier.classify_field(element, enhanced_context)
        
        # Enhance with Timothy-specific mappings
        if classification.fill_strategy.value == "simple_mapping" and not classification.mapped_to:
            # Try to find appropriate mapping
            element_lower = element.selector.lower()
            
            # Smart mapping based on element characteristics
            if "first" in element_lower or "fname" in element_lower:
                classification.mapped_to = "personal.first_name"
            elif "last" in element_lower or "lname" in element_lower:
                classification.mapped_to = "personal.last_name"
            elif "email" in element_lower:
                classification.mapped_to = "personal.email"
            elif "phone" in element_lower:
                classification.mapped_to = "personal.phone"
            elif "school" in element_lower or "university" in element_lower:
                classification.mapped_to = "education.school"
            elif "degree" in element_lower:
                classification.mapped_to = "education.degree"
            elif "gpa" in element_lower:
                classification.mapped_to = "education.gpa"
        
        # Add value from Timothy's profile if we have a mapping
        if classification.mapped_to and classification.mapped_to in self.field_mappings:
            classification.timothy_value = self.field_mappings[classification.mapped_to]
        
        return classification
    
    def get_value_for_field(self, classification) -> str:
        """Get the actual value to fill for a classified field"""
        
        if hasattr(classification, 'timothy_value'):
            return classification.timothy_value
        elif classification.mapped_to and classification.mapped_to in self.field_mappings:
            return self.field_mappings[classification.mapped_to]
        else:
            return ""

# Demo function
async def demo_timothy_integration():
    """Demo Timothy's profile integration with field classification"""
    
    print("🎯 Timothy Weaver Profile Integration Demo")
    print("=" * 60)
    
    # Initialize Timothy's profile processor
    timothy = TimothyProfileProcessor()
    
    print("👤 Profile Summary:")
    print(f"   Name: {timothy.profile.first_name} {timothy.profile.last_name}")
    print(f"   Email: {timothy.profile.email}")
    print(f"   Phone: {timothy.profile.phone}")
    print(f"   Education: {timothy.profile.current_degree} at {timothy.profile.current_school}")
    print(f"   GPA: {timothy.profile.gpa}")
    print(f"   Graduation: {timothy.profile.graduation_date}")
    print(f"   Skills: {', '.join(timothy.profile.primary_languages[:3])}...")
    
    print(f"\n📋 Available Field Mappings: {len(timothy.get_basic_info_mapping())}")
    
    # Show some key mappings
    mappings = timothy.get_basic_info_mapping()
    key_mappings = {
        "personal.first_name": mappings["personal.first_name"],
        "personal.email": mappings["personal.email"],
        "education.school": mappings["education.school"],
        "experience.years_programming": mappings["experience.years_programming"],
        "skills.programming_languages": mappings["skills.programming_languages"]
    }
    
    print("\n🔑 Key Field Mappings:")
    for key, value in key_mappings.items():
        print(f"   {key}: {value}")
    
    print(f"\n📝 Sample RAG Response (Why interested in position):")
    sample_response = timothy.generate_custom_response(
        "motivation", 
        "Why are you interested in this position?",
        {"name": "TechCorp", "values": ["innovation", "collaboration"], "focus": "AI-powered solutions"}
    )
    
    # Show first 200 characters
    print(f"   {sample_response[:200]}...")
    
    print(f"\n✅ Timothy's profile successfully integrated!")
    print(f"   • {len(timothy.get_basic_info_mapping())} field mappings available")
    print(f"   • Rich context for RAG generation")
    print(f"   • Custom responses for common questions")
    print(f"   • Ready for intelligent job application automation")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_timothy_integration())
