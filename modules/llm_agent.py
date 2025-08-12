from typing import Dict, List, Optional
import os
import groq
import logging
from dotenv import load_dotenv

load_dotenv()
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_llm():
    """Initialize Groq client with proper error handling"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    try:
        return groq.Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        raise


def generate_completion(client, prompt: str) -> str:
    """Generate completion using Groq with comprehensive error handling"""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        # Validate response structure
        if not completion.choices:
            raise ValueError("No completion choices returned from API")
        
        if not completion.choices[0].message:
            raise ValueError("No message in completion choice")
        
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("Empty content in completion")
        
        return content.strip()
        
    except groq.RateLimitError:
        logger.error("Rate limit exceeded for Groq API")
        raise
    except groq.AuthenticationError:
        logger.error("Authentication failed for Groq API")
        raise
    except groq.BadRequestError as e:
        logger.error(f"Bad request to Groq API: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during completion generation: {e}")
        raise


def map_industry_to_wordstream(industry: str, client) -> str:
    """Map user's industry to WordStream's dropdown options with fallback"""
    if not industry or not industry.strip():
        logger.warning("Empty industry provided, returning 'Business Services' as default")
        return "Business Services"
    
    # List of valid WordStream industries for validation
    valid_industries = [
        "Automotive", "Beauty & Personal Care", "Business Services", "Education",
        "Finance & Insurance", "Health & Medical", "Home & Garden", "Legal Services",
        "Real Estate", "Retail & E-commerce", "Technology", "Travel & Hospitality",
        "Food & Beverage", "Entertainment", "Non-profit", "Construction",
        "Manufacturing", "Agriculture", "Sports & Recreation"
    ]
    
    prompt = f"""Given the user's industry "{industry.strip()}", map it to the closest matching option from WordStream's industry dropdown.
    
    Valid WordStream industries:
    {chr(10).join([f"- {ind}" for ind in valid_industries])}
    
    Rules:
    1. Return only the exact matching industry name from the list above
    2. If no close match exists, return "Business Services"
    3. Do not include any explanation or additional text
    4. The response must be one of the valid industries listed above
    
    Industry to map: "{industry.strip()}" """
    
    try:
        mapped_industry = generate_completion(client, prompt)
        
        # Validate that the mapped industry is in our valid list
        if mapped_industry in valid_industries:
            logger.info(f"Successfully mapped '{industry}' to '{mapped_industry}'")
            return mapped_industry
        else:
            logger.warning(f"LLM returned invalid industry '{mapped_industry}', using 'Business Services'")
            return "Business Services"
            
    except Exception as e:
        logger.error(f"Failed to map industry '{industry}': {e}")
        logger.info("Falling back to 'Business Services'")
        return "Business Services"


def extract_form_data(config: Dict, llm) -> Dict:
    """Extract and prepare form data from config using LLM with robust error handling"""
    if not isinstance(config, dict):
        raise TypeError("Config must be a dictionary")
    
    # Initialize form data with defaults
    form_data = {
        "website": "",
        "industry": "Business Services",  # Default fallback
        "location": ""
    }
    
    # Extract website with validation
    website = config.get("brand_website", "")
    if isinstance(website, str):
        form_data["website"] = website.strip()
    else:
        logger.warning(f"Invalid website type: {type(website)}, using empty string")
    
    # Map industry - check multiple possible keys (case insensitive)
    industry_keys = ["Industry", "industry", "INDUSTRY", "business_type", "sector"]
    industry_found = False
    
    for key in industry_keys:
        if key in config and config[key]:
            try:
                form_data["industry"] = map_industry_to_wordstream(str(config[key]), llm)
                industry_found = True
                logger.info(f"Found industry using key '{key}': {config[key]}")
                break
            except Exception as e:
                logger.error(f"Failed to process industry from key '{key}': {e}")
                continue
    
    if not industry_found:
        logger.info("No valid industry found in config, using default 'Business Services'")
    
    # Extract location - check multiple possible keys
    location_keys = ["locations", "location", "address", "city", "primary_location"]
    location_found = False
    
    for key in location_keys:
        if key in config and config[key]:
            location_value = config[key]
            
            # Handle both list and string formats
            if isinstance(location_value, list) and location_value:
                form_data["location"] = str(location_value[0]).strip()
                location_found = True
                logger.info(f"Found location from list using key '{key}': {location_value[0]}")
                break
            elif isinstance(location_value, str) and location_value.strip():
                form_data["location"] = location_value.strip()
                location_found = True
                logger.info(f"Found location using key '{key}': {location_value}")
                break
    
    if not location_found:
        logger.info("No valid location found in config")
    
    # Log final form data (excluding sensitive info)
    logger.info(f"Extracted form data: industry='{form_data['industry']}', location='{form_data['location']}', website_provided={'Yes' if form_data['website'] else 'No'}")
    
    return form_data