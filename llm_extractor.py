"""
LLM-based job posting information extractor using Ollama with DeepSeek.
This module replaces regex-based extraction with AI-powered extraction.
"""

import json
import logging
from typing import Dict, List, Optional, Union, Any

import ollama

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the model to use
LLM_MODEL = "deepseek"  # Use DeepSeek model through Ollama

def extract_with_llm(text: str, extraction_type: str) -> List[str]:
    """
    Extract information from text using Ollama with DeepSeek LLM.
    
    Args:
        text (str): The text to extract information from.
        extraction_type (str): Type of information to extract (responsibilities, qualifications, etc.)
        
    Returns:
        List[str]: List of extracted items as bullet points.
    """
    try:
        # Define prompts based on extraction type
        if extraction_type == "responsibilities":
            system_prompt = """You are an expert job analyst. Extract the key job responsibilities from the provided job description. 
            Return the responsibilities as a JSON list of strings. Each responsibility should:
            1. Be concise (maximum 80 characters)
            2. Start with an action verb when possible
            3. Focus on one discrete task or duty
            4. Not include bullet points or numbering (these will be added later)
            
            Format your response as a valid JSON list like this:
            ["Responsibility 1", "Responsibility 2", "Responsibility 3"]
            
            Only return the JSON list, nothing else."""
            
        elif extraction_type == "qualifications":
            system_prompt = """You are an expert job analyst. Extract the key qualifications, requirements and skills needed for the position from the provided job description.
            Return the qualifications as a JSON list of strings. Each qualification should:
            1. Be concise (maximum 80 characters)
            2. Focus on one discrete qualification, skill, or requirement
            3. Not include bullet points or numbering (these will be added later)
            
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
            
        else:
            raise ValueError(f"Unknown extraction type: {extraction_type}")
        
        # Truncate text if too long (many LLMs have context limits)
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
        
        # Extract the response content
        result = response['message']['content']
        logger.debug(f"LLM response for {extraction_type}: {result}")
        
        # Try to parse JSON from the response
        try:
            # Find JSON list in the response (handles cases where model adds extra text)
            json_start = result.find('[')
            json_end = result.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
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
    """
    Fallback method when LLM extraction fails.
    Performs basic extraction based on keyword matching.
    
    Args:
        text (str): The text to extract information from.
        extraction_type (str): Type of information to extract
        
    Returns:
        List[str]: List of extracted items.
    """
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
    """
    Check if Ollama is available and the specified model is loaded.
    
    Returns:
        bool: True if Ollama is available and model is loaded, False otherwise.
    """
    try:
        response = ollama.list()
        available_models = [model['name'] for model in response.get('models', [])]
        
        if LLM_MODEL in available_models:
            logger.info(f"Ollama is available and {LLM_MODEL} model is loaded")
            return True
        else:
            logger.warning(f"Ollama is available but {LLM_MODEL} model is not loaded")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False