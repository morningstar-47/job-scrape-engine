import logging
import os
import sys
import json

# Add src to the system path to allow imports from src and src.modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from modules.llm_integration import LLMInteractionModule
from config import GROQ_API_KEY, GROQ_MODEL_NAME

# Set up logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TEST_LLM_MODULE")

def run_llm_module_test():
    """
    Tests the LLMInteractionModule by generating a consolidated email draft 
    using the Groq API with mock data and validating the structured output.
    """
    logger.info("--- Starting LLMInteractionModule Test (Groq Integration) ---")
    
    # Check 1: API Key Availability
    if not GROQ_API_KEY:
        logger.warning("SKIP: GROQ_API_KEY is not set. Skipping live Groq API test.")
        return

    # 2. Define Mock Input Data (List of job offers)
    mock_batch_data = [
        {"id_offre": "A101", "Title": "Senior Backend Developer", "Location": "Remote", "Salary": "$150k"},
        {"id_offre": "B202", "Title": "Data Scientist Internship", "Location": "Boston, MA", "Salary": "N/A"},
        {"id_offre": "C303", "Title": "Product Manager (AI)", "Location": "New York, NY", "Salary": "$180k+"}
    ]

    # 3. Initialize the LLM Module
    try:
        llm_module = LLMInteractionModule()
        logger.info(f"LLM Module initialized. Using model: {GROQ_MODEL_NAME}")
    except Exception as e:
        logger.error(f"FATAL: Failed to initialize LLMInteractionModule: {e}")
        return

    # 4. Call the generation method
    logger.info(f"Generating consolidated email for {len(mock_batch_data)} offers...")
    email_draft = llm_module.generate_consolidated_email(mock_batch_data)

    # 5. Validation and Assertions
    
    # Assertion 1: Check if a draft was returned
    if email_draft is None:
        logger.error("FAILURE: generate_consolidated_email returned None.")
        return

    # Assertion 2: Check type (should be a dict)
    if not isinstance(email_draft, dict):
        logger.error(f"FAILURE: Expected dict output, got {type(email_draft).__name__}.")
        return

    # Assertion 3: Check required keys (subject and body)
    if 'subject' not in email_draft or 'body' not in email_draft:
        logger.error("FAILURE: Output JSON is missing 'subject' or 'body' keys.")
        logger.debug(f"Received Draft: {json.dumps(email_draft, indent=2)}")
        return

    # Assertion 4: Check content length (should be substantial)
    if len(email_draft['body']) < 100:
        logger.error("FAILURE: Email body is too short, indicating potential failure in content generation.")
        logger.debug(f"Received Body: {email_draft['body']}")
        return
        
    logger.info("--- TEST SUCCESSFUL ---")
    logger.info("Successfully generated and parsed structured JSON output from Groq.")
    logger.info(f"Subject: {email_draft['subject']}")
    logger.info(f"Body Preview: {email_draft['body']}...")
    logger.info(f"The draft successfully contains the required keys and substantial content.")


if __name__ == "__main__":
    run_llm_module_test()