import re
import logging
from bs4 import BeautifulSoup
import trafilatura

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define skill-related keywords
SKILL_KEYWORDS = [
    "python", "javascript", "java", "c++", "c#", "ruby", "php", "sql", "nosql", 
    "mongodb", "postgresql", "mysql", "oracle", "aws", "azure", "gcp", "docker", 
    "kubernetes", "git", "terraform", "ansible", "jenkins", "ci/cd", "agile", 
    "scrum", "react", "angular", "vue", "node.js", "django", "flask", "spring", 
    "express", "html", "css", "sass", "less", "typescript", "jquery", "rest api", 
    "graphql", "machine learning", "ai", "data science", "big data", "hadoop", 
    "spark", "tableau", "power bi", "excel", "linux", "windows", "macos", 
    "networking", "security", "devops", "sre", "product management", "swift",
    "kotlin", "rust", "go", "scala", "perl", "bash", "powershell", "r", 
    "data analysis", "statistics", "jira", "confluence", "figma", "sketch",
    "adobe", "photoshop", "illustrator", "xd", "indesign", "marketing", "seo",
    "analytics", "leadership", "management", "communication", "problem-solving",
    "teamwork", "creativity", "critical thinking", "frontend", "backend", "fullstack"
]

# Define experience requirement patterns
EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s+years?\s+(?:of\s+)?experience",
    r"experience\s*(?:of|:)?\s*(\d+)\+?\s+years?",
    r"minimum\s+(?:of\s+)?(\d+)\+?\s+years?\s+(?:of\s+)?experience",
    r"at\s+least\s+(\d+)\+?\s+years?\s+(?:of\s+)?experience"
]

# Define location patterns
LOCATION_PATTERNS = [
    r"location\s*(?::|is)?\s*(.*?)(?:\.|,|\n)",
    r"based\s+in\s+(.*?)(?:\.|,|\n)",
    r"position\s+is\s+(?:located\s+)?in\s+(.*?)(?:\.|,|\n)",
    r"job\s+location\s*(?::|is)?\s*(.*?)(?:\.|,|\n)"
]

# Define role type patterns (individual contributor vs team lead)
ROLE_TYPE_KEYWORDS = {
    'individual_contributor': [
        "individual contributor", "ic ", "developer", "engineer", "specialist",
        "analyst", "consultant", "designer", "writer", "contributor", "associate"
    ],
    'team_lead': [
        "team lead", "manager", "director", "supervisor", "head of", "chief",
        "lead ", "principal", "senior", "architect", "vp", "executive", "leader"
    ]
}

def extract_job_details(html_content, url):
    """
    Extract job details from HTML content.
    
    Args:
        html_content (str): The HTML content of the job posting.
        url (str): The URL of the job posting.
        
    Returns:
        dict: The extracted job details.
    """
    # Extract plain text from HTML for text-based analysis
    logger.debug("Extracting plain text from HTML content")
    
    # Try to extract text using trafilatura first
    plain_text = trafilatura.extract(html_content)
    
    # If trafilatura fails, fallback to BeautifulSoup
    if not plain_text:
        soup = BeautifulSoup(html_content, 'html.parser')
        plain_text = soup.get_text(separator=' ', strip=True)
    
    # Create BeautifulSoup object for structure-based analysis
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize the result dictionary
    job_details = {
        'title': extract_job_title(soup, plain_text),
        'company': extract_company_name(soup, plain_text),
        'skills': extract_skills(plain_text),
        'experience': extract_experience(plain_text),
        'location': extract_location(soup, plain_text),
        'role_type': determine_role_type(plain_text),
        'description_excerpt': extract_description_excerpt(plain_text),
        'responsibilities': extract_responsibilities(plain_text),
        'qualifications': extract_qualifications(plain_text)
    }
    
    logger.debug(f"Extracted job details: {job_details}")
    return job_details

def extract_job_title(soup, plain_text):
    """Extract the job title from the page."""
    # Try common HTML patterns first
    title_candidates = []
    
    # Look for h1 elements that might contain the job title
    h1_elements = soup.find_all('h1')
    for h1 in h1_elements:
        title_candidates.append(h1.get_text(strip=True))
    
    # Look for title in meta tags
    meta_title = soup.find('meta', property='og:title')
    if meta_title and meta_title.get('content'):
        title_candidates.append(meta_title['content'])
    
    # Try to find elements with 'job-title' or similar in class or id
    job_title_elements = soup.find_all(class_=lambda c: c and 'job-title' in c.lower())
    job_title_elements += soup.find_all(id=lambda i: i and 'job-title' in i.lower())
    for element in job_title_elements:
        title_candidates.append(element.get_text(strip=True))
    
    # Look for the first non-empty candidate
    for title in title_candidates:
        if title and len(title) < 100:  # Sanity check on title length
            return title
    
    # Fallback: try to extract from plain text
    title_match = re.search(r"(?:job title|position)(?:\s*:\s*|\s+is\s+)(.*?)(?:\.|,|\n)", 
                           plain_text, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()
    
    return "Job Title Not Found"

def extract_company_name(soup, plain_text):
    """Extract the company name from the page."""
    # Try common HTML patterns first
    company_candidates = []
    
    # Look for company in meta tags
    meta_company = soup.find('meta', property='og:site_name')
    if meta_company and meta_company.get('content'):
        company_candidates.append(meta_company['content'])
    
    # Try to find elements with 'company-name' or similar in class or id
    company_elements = soup.find_all(class_=lambda c: c and 'company' in c.lower())
    company_elements += soup.find_all(id=lambda i: i and 'company' in i.lower())
    for element in company_elements:
        company_candidates.append(element.get_text(strip=True))
    
    # Look for the first non-empty candidate
    for company in company_candidates:
        if company and len(company) < 50:  # Sanity check on company name length
            return company
    
    # Fallback: try to extract from plain text
    company_match = re.search(r"(?:company|organization)(?:\s*:\s*|\s+is\s+)(.*?)(?:\.|,|\n)", 
                             plain_text, re.IGNORECASE)
    if company_match:
        return company_match.group(1).strip()
    
    return "Company Name Not Found"

def extract_skills(text):
    """Extract skills from text using a combination of predefined keywords and dynamic extraction."""
    found_skills = []
    text_lower = text.lower()
    
    # First pass: Use the predefined skills list
    for skill in SKILL_KEYWORDS:
        skill_lower = skill.lower()
        # Use word boundary to match whole words only
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    
    # Find skills in common sections like "Requirements" or "Qualifications"
    skill_sections_patterns = [
        r'(?:requirements|qualifications|skills needed|what you\'ll need|what you need|skills|technical skills|technical requirements)(?::|.{0,10})\s*(.*?)(?:(?:\n\n)|responsibilities|about the role|about us|what we offer|benefits)',
        r'(?:experience|expertise|proficiency)(?::|.{0,10})\s*(.*?)(?:(?:\n\n)|responsibilities|qualifications|about the role|about us|what we offer|benefits)'
    ]
    
    skill_sections = []
    for pattern in skill_sections_patterns:
        sections = re.findall(pattern, text_lower, re.DOTALL)
        skill_sections.extend(sections)
    
    if skill_sections:
        for section in skill_sections:
            # Extract bullet points or list items 
            bullet_items = re.findall(r'(?:•|-|\*|\d+\.)\s*(.*?)(?:\n|$)', section)
            
            # If no bullet points found, try to split by sentences or commas
            if not bullet_items:
                # Try to split by sentences first
                sentences = re.split(r'(?<=[.!?])\s+', section)
                bullet_items = [s.strip() for s in sentences if s.strip()]
            
            for item in bullet_items:
                item = item.strip()
                if not item:
                    continue
                
                # Look for technical skills in the bullet point
                # First check if any known skills are mentioned
                for skill in SKILL_KEYWORDS:
                    skill_lower = skill.lower()
                    if (f" {skill_lower} " in f" {item.lower()} " or 
                        item.lower().startswith(skill_lower + " ") or 
                        item.lower().endswith(" " + skill_lower)) and skill not in found_skills:
                        found_skills.append(skill)
                
                # Then look for potential new skills (technical terms often have specific patterns)
                # Look for terms that might be technologies, programming languages, frameworks, etc.
                potential_skills = re.findall(r'\b([A-Z][a-zA-Z0-9]*(?:\s[A-Z][a-zA-Z0-9]*)*|[A-Za-z0-9]+\+\+|[A-Za-z0-9]+\#|[a-z][a-zA-Z0-9]+(?:\.js|\.NET))\b', item)
                for skill in potential_skills:
                    skill = skill.strip()
                    # Ignore very common words and short terms
                    if (len(skill) > 2 and 
                        skill.lower() not in ['the', 'and', 'for', 'with', 'using', 'have', 'has', 'had', 'our', 'that', 'this'] and
                        skill not in found_skills):
                        found_skills.append(skill)
                        
                # Extract technical terms from the item
                # Look for phrases like "experience with X", "knowledge of X", etc.
                experience_patterns = [
                    r'experience (?:with|in|using) ([^,.;]+)',
                    r'knowledge of ([^,.;]+)',
                    r'proficiency in ([^,.;]+)',
                    r'familiarity with ([^,.;]+)',
                    r'expertise in ([^,.;]+)',
                    r'understanding of ([^,.;]+)',
                    r'skilled in ([^,.;]+)',
                    r'proficient in ([^,.;]+)'
                ]
                
                for pattern in experience_patterns:
                    matches = re.findall(pattern, item.lower())
                    for match in matches:
                        # Split by 'and' or commas to get individual skills
                        skills_parts = re.split(r'\s+and\s+|,\s*', match)
                        for part in skills_parts:
                            part = part.strip()
                            if part and len(part) > 2 and part not in found_skills:
                                found_skills.append(part)
    
    # Remove duplicates while preserving case
    unique_skills = []
    lower_skills = set()
    
    for skill in found_skills:
        if skill.lower() not in lower_skills:
            lower_skills.add(skill.lower())
            unique_skills.append(skill)
    
    return sorted(unique_skills) if unique_skills else ["No specific skills identified"]

def extract_experience(text):
    """Extract experience requirements from text."""
    # Look for patterns like "X years of experience"
    for pattern in EXPERIENCE_PATTERNS:
        experience_match = re.search(pattern, text, re.IGNORECASE)
        if experience_match:
            years = experience_match.group(1)
            return f"{years}+ years of experience required"
    
    # Check for more general mentions of experience
    if re.search(r'\bentry[\s-]level\b', text, re.IGNORECASE):
        return "Entry-level position"
    if re.search(r'\bjunior\b', text, re.IGNORECASE):
        return "Junior-level position"
    if re.search(r'\bsenior\b', text, re.IGNORECASE):
        return "Senior-level position"
    if re.search(r'\bexperienced\b', text, re.IGNORECASE):
        return "Experience required (unspecified years)"
    
    return "Experience requirements not clearly specified"

def extract_location(soup, text):
    """Extract job location from the page."""
    # Try to find location in structured HTML first
    location_candidates = []
    
    # Look for elements with 'location' in class or id
    location_elements = soup.find_all(class_=lambda c: c and 'location' in c.lower())
    location_elements += soup.find_all(id=lambda i: i and 'location' in i.lower())
    for element in location_elements:
        location_candidates.append(element.get_text(strip=True))
    
    # Check for location in meta tags
    meta_location = soup.find('meta', property='og:location')
    if meta_location and meta_location.get('content'):
        location_candidates.append(meta_location['content'])
    
    # Look for the first non-empty candidate
    for location in location_candidates:
        if location and len(location) < 100:  # Sanity check on location length
            return location
    
    # Try text-based pattern matching
    for pattern in LOCATION_PATTERNS:
        location_match = re.search(pattern, text, re.IGNORECASE)
        if location_match:
            return location_match.group(1).strip()
    
    # Check for common location indicators
    if re.search(r'\bremote\b', text, re.IGNORECASE):
        return "Remote"
    if re.search(r'\bhybrid\b', text, re.IGNORECASE):
        return "Hybrid"
    if re.search(r'\bon[\s-]site\b', text, re.IGNORECASE) or re.search(r'\bin[\s-]office\b', text, re.IGNORECASE):
        return "On-site (location not specified)"
    
    return "Location not clearly specified"

def determine_role_type(text):
    """Determine if the role is for an individual contributor or team lead."""
    text_lower = text.lower()
    
    # Count occurrences of key phrases for each role type
    ic_count = 0
    lead_count = 0
    
    for keyword in ROLE_TYPE_KEYWORDS['individual_contributor']:
        ic_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
    
    for keyword in ROLE_TYPE_KEYWORDS['team_lead']:
        lead_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
    
    # Look for specific indicators of management responsibility
    manages_team = re.search(r'\b(?:manage|lead|supervise)(?:s|ing)?\s+(?:a\s+)?team\b', text_lower)
    if manages_team:
        lead_count += 3  # Give extra weight to explicit mentions of team management
    
    # Look for phrases about working independently
    works_independently = re.search(r'\b(?:work(?:s|ing)?\s+independently|individual\s+contributor)\b', text_lower)
    if works_independently:
        ic_count += 3  # Give extra weight to explicit mentions of working independently
    
    # Determine the role type based on counts
    if lead_count > ic_count * 1.5:  # If lead indicators are significantly more common
        return "Team Lead/Manager"
    elif ic_count > lead_count:
        return "Individual Contributor"
    else:
        # Check for special cases
        if "manager" in text_lower or "director" in text_lower or "lead" in text_lower:
            return "Team Lead/Manager"
        return "Role type unclear (possibly both IC and leadership aspects)"

def extract_description_excerpt(text, max_length=200):
    """Extract a short excerpt from the job description."""
    # Try to find the start of the job description
    desc_start_patterns = [
        r'job description(?:\s*:|\s+)(.*)',
        r'about the (?:job|role|position)(?:\s*:|\s+)(.*)',
        r'what you\'ll (?:do|be doing)(?:\s*:|\s+)(.*)',
        r'responsibilities(?:\s*:|\s+)(.*)'
    ]
    
    for pattern in desc_start_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            excerpt = match.group(1).strip()
            # Truncate and add ellipsis if needed
            if len(excerpt) > max_length:
                excerpt = excerpt[:max_length-3] + "..."
            return excerpt
    
    # If no specific section found, use the beginning of the text
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def extract_responsibilities(text):
    """Extract key responsibilities from the job description."""
    # Check for specific standalone "Key Responsibilities:" section first - very specific pattern
    standalone_match = re.search(r'Key\s+Responsibilities\s*:\s*\n\s*((?:.+\n)+?)(?:\n\n|\n\s*Qualifications)', 
                               text, re.IGNORECASE | re.DOTALL)
    
    # If that doesn't work, try a more general pattern
    if not standalone_match:
        standalone_match = re.search(r'key\s+responsibilities\s*:?\s*\n((?:.+\n)+?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))', 
                                text, re.IGNORECASE | re.DOTALL)
    
    if standalone_match:
        responsibilities_text = standalone_match.group(1).strip()
        # Process the found text into bullet points
        bullet_items = re.findall(r'(?:•|-|\*|\d+\.)\s*(.*?)(?:\n|$)', responsibilities_text)
        
        # If the text doesn't have bullet formatting, each line might be a responsibility
        if not bullet_items:
            lines = [line.strip() for line in responsibilities_text.split('\n') if line.strip()]
            if lines:
                formatted_responsibilities = ["• " + line for line in lines]
                return formatted_responsibilities
    
    # Define more general patterns to look for responsibility sections
    responsibility_patterns = [
        # Various header formats
        r'(?:key\s+)?responsibilities(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))',
        r'(?:key\s+)?duties(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))',
        r'what\s+you\'ll\s+(?:do|be\s+doing)(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))',
        r'job\s+(?:duties|functions)(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))',
        r'the\s+role(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))',
        r'responsibilities\s+and\s+duties(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))',
        r'primary\s+responsibilities(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:qualifications|requirements|skills|about|apply|benefits|$))'
    ]
    
    for pattern in responsibility_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            responsibilities_text = match.group(1).strip()
            
            # Extract bullet points or numbered items
            bullet_items = re.findall(r'(?:•|-|\*|\d+\.)\s*(.*?)(?:\n|$)', responsibilities_text)
            
            # If no bullet points found, try to split by sentences or newlines
            if not bullet_items:
                # First try to split by newlines, as each line might be a separate responsibility
                lines = [line.strip() for line in responsibilities_text.split('\n') if line.strip()]
                if lines:
                    formatted_responsibilities = ["• " + line for line in lines]
                    return formatted_responsibilities
                
                # If that doesn't work, try to split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', responsibilities_text)
                bullet_items = [s.strip() for s in sentences if s.strip()]
            
            # Format as a list with bullet points - keep them concise
            if bullet_items:
                formatted_responsibilities = []
                for item in bullet_items:
                    item = item.strip()
                    if not item:
                        continue
                    # Limit to a reasonable length
                    if len(item) > 80:
                        # Try to truncate at a logical point
                        truncated = item[:80].rsplit(' ', 1)[0] + "..."
                        formatted_responsibilities.append("• " + truncated)
                    else:
                        formatted_responsibilities.append("• " + item)
                return formatted_responsibilities[:10]  # Limit to 10 items
            
            # If no structured format found, try to break into smaller chunks
            sentences = re.split(r'(?<=[.!?])\s+', responsibilities_text)
            if sentences:
                formatted_sentences = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence or len(sentence) < 10:
                        continue
                    # Limit to a reasonable length
                    if len(sentence) > 80:
                        truncated = sentence[:80].rsplit(' ', 1)[0] + "..."
                        formatted_sentences.append("• " + truncated)
                    else:
                        formatted_sentences.append("• " + sentence)
                if formatted_sentences:
                    return formatted_sentences[:8]  # Limit to 8 to avoid overwhelming
            
            # Last resort - extract key phrases
            keywords = ["manage", "develop", "create", "implement", "support", "collaborate"]
            phrases = []
            for keyword in keywords:
                matches = re.finditer(rf'\b{keyword}\b.*?\.', responsibilities_text, re.IGNORECASE)
                for match in matches:
                    phrase = match.group(0).strip()
                    if 10 < len(phrase) < 80:
                        phrases.append("• " + phrase)
            if phrases:
                return phrases[:8]
                
            # If all else fails, return a chunked version of the text
            if len(responsibilities_text) > 80:
                chunks = [responsibilities_text[i:i+80] for i in range(0, len(responsibilities_text), 80)]
                return ["• " + chunk + "..." for chunk in chunks[:5]]
            return ["• " + responsibilities_text]
    
    # If still not found, look for any paragraph that seems to describe job duties
    # This is a fallback approach with looser pattern matching
    fallback_patterns = [
        r'(?:manage|lead|develop|design|create|implement|maintain|support|collaborate|analyze|report|communicate|oversee|direct|drive|ensure|provide|work|build)(.*?)(?:\.|$)',
        r'(?:responsible for|in charge of|duties include|will be working on)(.*?)(?:\.|$)'
    ]
    
    found_duties = []
    for pattern in fallback_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            duty = match.group(0).strip()
            if duty and len(duty) > 15 and len(duty) < 200:  # Reasonable length for a responsibility
                found_duties.append("• " + duty)
    
    if found_duties:
        return found_duties[:8]  # Limit to first 8 to avoid too many false positives
    
    # Last resort - try to look for lines that might be responsibilities based on verb patterns
    lines = text.split('\n')
    verb_pattern = r'^(?:Lead|Manage|Develop|Design|Create|Implement|Maintain|Support|Collaborate|Analyze|Report|Communicate|Oversee|Direct|Drive|Ensure|Provide|Work|Build|Architect|Optimize)'
    
    verb_lines = []
    for line in lines:
        if re.match(verb_pattern, line.strip(), re.IGNORECASE) and len(line.strip()) > 15:
            verb_lines.append("• " + line.strip())
    
    if verb_lines:
        return verb_lines[:8]  # Limit to avoid false positives
    
    # If no responsibility section found
    return ["No specific responsibilities section found in the job posting."]

def extract_qualifications(text):
    """Extract qualifications and skills requirements from the job description."""
    # Check for specific standalone "Qualifications & Skills:" section first - very specific pattern
    standalone_match = re.search(r'Qualifications\s+&\s+Skills\s*:\s*\n\s*((?:.+\n)+?)(?:\n\n|\nLocation)', 
                           text, re.IGNORECASE | re.DOTALL)
    
    # If that doesn't work, try a more general pattern
    if not standalone_match:
        standalone_match = re.search(r'(?:qualifications\s*(?:&|and)?\s*skills|skills\s*(?:&|and)?\s*qualifications)\s*:?\s*\n((?:.+\n)+?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))', 
                                text, re.IGNORECASE | re.DOTALL)
    
    if standalone_match:
        qualifications_text = standalone_match.group(1).strip()
        # Process the found text into bullet points
        bullet_items = re.findall(r'(?:•|-|\*|\d+\.)\s*(.*?)(?:\n|$)', qualifications_text)
        
        # If the text doesn't have bullet formatting, each line might be a qualification
        if not bullet_items:
            lines = [line.strip() for line in qualifications_text.split('\n') if line.strip()]
            if lines:
                formatted_qualifications = ["• " + line for line in lines]
                return formatted_qualifications
    
    # Define more general patterns to look for qualification sections
    qualification_patterns = [
        # Various header formats
        r'(?:key\s+)?qualifications(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'(?:key\s+)?requirements(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'skills(?:\s+required|needed)?(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'what\s+you\'ll\s+need(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'we\'re\s+looking\s+for(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'(?:candidate|applicant)\s+requirements(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'(?:required|preferred)\s+qualifications(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))',
        r'experience\s+(?:required|needed)(?:\s*:|\s*\n)(.*?)(?:\n\n|\n\s*(?:responsibilities|about|apply|benefits|company|compensation|$))'
    ]
    
    for pattern in qualification_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            qualifications_text = match.group(1).strip()
            
            # Extract bullet points or numbered items
            bullet_items = re.findall(r'(?:•|-|\*|\d+\.)\s*(.*?)(?:\n|$)', qualifications_text)
            
            # If no bullet points found, try to split by sentences or newlines
            if not bullet_items:
                # First try to split by newlines, as each line might be a separate qualification
                lines = [line.strip() for line in qualifications_text.split('\n') if line.strip()]
                if lines:
                    formatted_qualifications = []
                    for line in lines:
                        if not line or len(line) < 10:
                            continue
                        # Limit to a reasonable length
                        if len(line) > 80:
                            truncated = line[:80].rsplit(' ', 1)[0] + "..."
                            formatted_qualifications.append("• " + truncated)
                        else:
                            formatted_qualifications.append("• " + line)
                    if formatted_qualifications:
                        return formatted_qualifications[:10]
                
                # If that doesn't work, try to split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', qualifications_text)
                bullet_items = [s.strip() for s in sentences if s.strip()]
            
            # Format as a list with bullet points - keep them concise
            if bullet_items:
                formatted_qualifications = []
                for item in bullet_items:
                    item = item.strip()
                    if not item:
                        continue
                    # Limit to a reasonable length
                    if len(item) > 80:
                        # Try to truncate at a logical point
                        truncated = item[:80].rsplit(' ', 1)[0] + "..."
                        formatted_qualifications.append("• " + truncated)
                    else:
                        formatted_qualifications.append("• " + item)
                return formatted_qualifications[:10]  # Limit to 10 items
            
            # If no structured format found, try to break into smaller chunks
            sentences = re.split(r'(?<=[.!?])\s+', qualifications_text)
            if sentences:
                formatted_sentences = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence or len(sentence) < 10:
                        continue
                    # Limit to a reasonable length
                    if len(sentence) > 80:
                        truncated = sentence[:80].rsplit(' ', 1)[0] + "..."
                        formatted_sentences.append("• " + truncated)
                    else:
                        formatted_sentences.append("• " + sentence)
                if formatted_sentences:
                    return formatted_sentences[:8]  # Limit to 8 to avoid overwhelming
            
            # Last resort - extract key phrases
            keywords = ["experience", "knowledge", "degree", "skills", "proficient", "education"]
            phrases = []
            for keyword in keywords:
                matches = re.finditer(rf'\b{keyword}\b.*?\.', qualifications_text, re.IGNORECASE)
                for match in matches:
                    phrase = match.group(0).strip()
                    if 10 < len(phrase) < 80:
                        phrases.append("• " + phrase)
            if phrases:
                return phrases[:8]
                
            # If all else fails, return a chunked version of the text
            if len(qualifications_text) > 80:
                chunks = [qualifications_text[i:i+80] for i in range(0, len(qualifications_text), 80)]
                return ["• " + chunk + "..." for chunk in chunks[:5]]
            return ["• " + qualifications_text]
    
    # If still not found, look for any paragraph that seems to describe qualifications
    # This is a fallback approach with looser pattern matching
    fallback_patterns = [
        r'(?:must have|should have|requires|required|proficient in|expertise in|experience with|knowledge of|familiarity with)(.*?)(?:\.|$)',
        r'(?:degree in|education in|background in|certification in|qualified in)(.*?)(?:\.|$)',
        r'(?:you have|you are|you will have|you should have|bachelor\'s|master\'s|phd)(.*?)(?:\.|$)'
    ]
    
    found_qualifications = []
    for pattern in fallback_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            qualification = match.group(0).strip()
            if qualification and len(qualification) > 15 and len(qualification) < 200:  # Reasonable length
                found_qualifications.append("• " + qualification)
    
    if found_qualifications:
        return found_qualifications[:8]  # Limit to avoid too many false positives
    
    # Last resort - look for common patterns of qualifications by keyword
    keywords = ['experience', 'knowledge', 'degree', 'education', 'skill', 'proficiency', 'certification', 'understanding']
    
    keyword_qualifications = []
    lines = text.split('\n')
    for line in lines:
        for keyword in keywords:
            if keyword in line.lower() and len(line.strip()) > 15 and len(line.strip()) < 200:
                keyword_qualifications.append("• " + line.strip())
                break  # Only add each line once
    
    if keyword_qualifications:
        return keyword_qualifications[:8]  # Limit to avoid false positives
    
    # If no qualification section found
    return ["No specific qualifications section found in the job posting."]
