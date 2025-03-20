"""
LLM-based job posting information extractor using Ollama with DeepSeek.
This module replaces regex-based extraction with AI-powered extraction.
"""

import json
import logging
from typing import Dict, List, Optional, Union, Any

import ollama

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Define the model to use
LLM_MODEL = "llama3.2:latest"


def extract_with_llm(text: str, extraction_type: str) -> List[str]:
    try:
        if extraction_type == "responsibilities":
            system_prompt = """You are an expert job analyst. Extract key job responsibilities from the provided job description.
                Rules for Responsibilities:
                1. extract major skills/ tools/experience needed as 3-4 word pointers
                   
                Response Format:
                Return a **valid JSON list** like this:  
                ["Responsibility 1", "Responsibility 2", "Responsibility 3"]
                
                Only return the JSON list, nothing else.**
            """
            
        elif extraction_type == "qualifications":
            system_prompt = """You are an expert job analyst. Extract the key qualifications, requirements and skills needed for the position from the provided job description.
            Return the qualifications as a JSON list of strings. Each qualification should:
                1. extract major skills and tools alog with experience needed as 3-4 word pointers
            
            Format your response as a valid JSON list like this:
            ["Qualification 1", "Qualification 2", "Qualification 3"]
            
            Only return the JSON list, nothing else."""
            
        elif extraction_type == "skills":
            system_prompt = """You are an expert job analyst. Extract the technical and soft skills required from the provided job description.
            Return the skills as a JSON list of strings. Each skill should:
            1. Be concise (one or a few words per skill)
            2. Focus on specific technical or soft skills
            3. Not include bullet points or numbering
            
            Format your response as a valid JSON list like this:
            ["Skill 1", "Skill 2", "Skill 3"]
            
            Only return the JSON list, nothing else."""
            
        elif extraction_type == "experience":
            system_prompt = """You are an expert job analyst. Extract the years of experience required from the provided job description.
            Consider phrases like "X years of experience", "entry-level", "junior", "senior", etc.
            
            Format your response as a single string, such as:
            "3+ years of experience required"
            "Entry-level position"
            "Senior-level position (5+ years experience)"
            
            Only return the experience requirement as a string, nothing else."""
            
        elif extraction_type == "role_type":
            system_prompt = """You are an expert job analyst. Determine if the role is primarily an individual contributor role 
            or a team lead/management role based on the job description.
            
            Format your response as one of the following strings:
            "Individual Contributor" - for roles focused on individual work rather than managing others
            "Team Lead/Manager" - for roles with people management or leadership responsibilities
            "Role type unclear (possibly both IC and leadership aspects)" - if it has elements of both
            
            Only return one of these three options as a string, nothing else."""
            
        else:
            raise ValueError(f"Unknown extraction type: {extraction_type}")
        
        max_text_length = 15000
        if len(text) > max_text_length:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {max_text_length} chars")
            text = text[:max_text_length]
        
        # Make request to Ollama
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Job description text:\n\n{text}\n\nExtract the {extraction_type}."
                }
            ]
        )
        
        result = response['message']['content']
        logger.debug(f"LLM response for {extraction_type}: {result}")

        try:
            # Find JSON list in the response (handles cases where model adds extra text)
            json_start = result.find('[')
            json_end = result.rfind(']') + 1

            if 0 <= json_start < json_end:
                json_str = result[json_start:json_end]
                parsed_list = json.loads(json_str)
                
                # Format as bullet points
                return [item for item in parsed_list if item.strip()]
            
            logger.warning(f"Could not find JSON list in response: {result}")
            return fallback_extraction(text, extraction_type)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {result}")
            return fallback_extraction(text, extraction_type)
            
    except Exception as e:
        logger.error(f"Error in LLM extraction: {e}")
        return fallback_extraction(text, extraction_type)


def fallback_extraction(text: str, extraction_type: str) -> List[str]:
    logger.info(f"Using fallback extraction for {extraction_type}")

    if extraction_type == "responsibilities":
        keywords = ["responsible", "role", "duties", "will", "manage", "lead", "develop"]
    elif extraction_type == "qualifications":
        keywords = ["required", "qualification", "experience", "degree", "skill", "knowledge"]
    elif extraction_type == "skills":
        keywords = ["python", "java", "javascript", "aws", "azure", "agile", "communication"]
    else:
        keywords = []
    
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    results = []
    
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in keywords):
            # Limit length to 80 chars
            if len(sentence) > 80:
                sentence = sentence[:77] + "..."
            results.append(sentence)
    
    # Return top results with bullet points added
    return [f"• {item}" for item in results[:8]]


def check_ollama_available() -> bool:
    try:
        response = ollama.list()

        if not response or "models" not in response:
            logger.error("Failed to retrieve model list from Ollama.")
            return False

        available_models = [model.get("model", "") for model in response.get("models", [])]

        if LLM_MODEL in available_models:
            logger.info(f"✅ Ollama is available and model '{LLM_MODEL}' is loaded.")
            return True
        else:
            logger.warning(f"⚠️ Ollama is available, but model '{LLM_MODEL}' is not loaded. Available models: {available_models}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to connect to Ollama: {e}")
        logger.warning("⚠️ Will use fallback extraction methods instead of LLM.")
        return False


if __name__ == '__main__':
    check_ollama_available()
    text = '''
    • Proven track record in building and leading engineering teams.
    
    • Strong technical and product acumen with experience in internet-scale products/services across platforms (Mobile, Web, Backend).
    
    • Experience with distributed systems and microservices architectures in the Cloud (AWS/Azure/GCP).
    
    • Solid fundamentals in system design, OOP, design patterns, and non-functional requirements.
    
    • Exposure to the full product lifecycle: design, development, testing, CI/CD, monitoring, and maintenance.
    
    • Excellent communication skills, with the ability to present clearly at all levels.
    
    • Comfortable in a fast-paced, agile startup environment with a strong customer focus.     '''
    print(extract_with_llm(text, 'qualifications'))