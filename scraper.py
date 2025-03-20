import time
import logging
import requests
from requests.exceptions import RequestException
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Headers to mimic a browser visit
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def scrape_job_posting(url):
    """
    Scrape the job posting from the provided URL.
    
    Args:
        url (str): The URL of the job posting to scrape.
        
    Returns:
        str: The HTML content of the job posting page or None if failed.
    """
    try:
        logger.info(f"Attempting to scrape: {url}")
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid URL: {url}")
            return None
        
        # Use trafilatura to fetch the URL
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            # Fallback to requests if trafilatura fails
            logger.warning("Trafilatura fetch failed, falling back to requests")
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
            response.raise_for_status()
            html_content = response.text
        else:
            html_content = downloaded
        
        # Add a small delay to be respectful to the website
        time.sleep(1)
        
        return html_content
    
    except RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}")
        return None

def extract_plain_text(html_content):
    """
    Extract plain text from HTML content using trafilatura.
    
    Args:
        html_content (str): The HTML content to extract text from.
        
    Returns:
        str: The extracted plain text.
    """
    try:
        text = trafilatura.extract(html_content)
        if not text:
            # Fallback to BeautifulSoup if trafilatura extraction fails
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        logger.error(f"Error extracting plain text: {str(e)}")
        # Fallback to BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except:
            return ""
