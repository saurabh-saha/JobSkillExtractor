import re
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_responsibilities(text):
    """Extract key responsibilities from the job description."""
    # Check for specific standalone "Key Responsibilities:" section first
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
    
    # More patterns and fallbacks here...
    return ["No specific responsibilities section found in the job posting."]

def extract_qualifications(text):
    """Extract qualifications and skills requirements from the job description."""
    # Check for specific standalone "Qualifications & Skills:" section first
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
    
    # More patterns and fallbacks here...
    return ["No specific qualifications section found in the job posting."]

# Test with the job posting text
with open('test_job_posting.txt', 'r') as f:
    content = f.read()

# Extract and print responsibilities
print("\nExtracted Responsibilities:\n")
responsibilities = extract_responsibilities(content)
for resp in responsibilities:
    print(resp)

# Extract and print qualifications
print("\nExtracted Qualifications:\n")
qualifications = extract_qualifications(content)
for qual in qualifications:
    print(qual)
