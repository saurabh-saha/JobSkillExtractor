import re

def extract_responsibilities_direct(text):
    # First try looking for a "Key Responsibilities:" section header exactly
    key_resp_match = re.search(r'Key\s+Responsibilities\s*:\s*\n\s*((?:.+\n)+?)(?:\n\n|\n\s*Qualifications)', 
                               text, re.IGNORECASE | re.DOTALL)
    
    if key_resp_match:
        resp_text = key_resp_match.group(1).strip()
        lines = [line.strip() for line in resp_text.split('\n') if line.strip()]
        return ["• " + line for line in lines]
    
    return ["No responsibilities section found"]

def extract_qualifications_direct(text):
    # Try looking for "Qualifications & Skills:" section header exactly
    qual_match = re.search(r'Qualifications\s+&\s+Skills\s*:\s*\n\s*((?:.+\n)+?)(?:\n\n|\nLocation)', 
                           text, re.IGNORECASE | re.DOTALL)
    
    if qual_match:
        qual_text = qual_match.group(1).strip()
        lines = [line.strip() for line in qual_text.split('\n') if line.strip()]
        return ["• " + line for line in lines]
    
    return ["No qualifications section found"]

# Sample job posting text that closely matches the format you provided
job_posting = """
Engineering Manager ($50K - $150K)

CodeRound AI is at the forefront of AI innovation, developing cutting-edge language models and AI solutions. We're seeking an experienced Engineering Manager to lead our growing team of AI engineers.

Key Responsibilities:

Lead and mentor a team of engineers in designing and deploying AI-driven applications.
Architect, develop, and optimize LLM-based AI solutions for real-world use cases.
Collaborate with data scientists, engineers, and product teams to build scalable AI pipelines.
Optimize AI models for performance, accuracy, and cost-efficiency.
Work with APIs, vector databases, and retrieval-augmented generation (RAG) techniques.
Ensure code quality, security, and best engineering practices in development workflows.
Stay updated with emerging AI/ML technologies and industry trends to drive innovation.
Provide technical guidance on AI infrastructure, model deployment, and DevOps practices.

Qualifications & Skills:

3+ years of experience in engineering management, preferably in AI/ML domains
Strong programming skills in Python and experience with AI frameworks (PyTorch, TensorFlow)
Proven track record of delivering production-ready AI applications
Experience with modern LLM deployment techniques, including prompt engineering
Familiarity with cloud platforms (AWS, GCP, Azure) and containerization (Docker, Kubernetes)
Understanding of DevOps practices and CI/CD pipelines for ML/AI systems
Excellent communication and leadership skills, with ability to translate technical concepts
Bachelor's degree in Computer Science, Engineering, or related field (or equivalent experience)

Location: Remote, with periodic in-person meetings at our India office

We offer competitive compensation, equity, flexible work arrangements, and the opportunity to work on cutting-edge AI technology that impacts millions of users.
"""

print("\nExtracted Responsibilities:\n")
for resp in extract_responsibilities_direct(job_posting):
    print(resp)

print("\nExtracted Qualifications:\n")
for qual in extract_qualifications_direct(job_posting):
    print(qual)
