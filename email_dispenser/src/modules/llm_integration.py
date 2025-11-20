import json
import logging
import time
import os
from typing import Dict, Any, List
# Import the Groq Python SDK and its specific error types
from groq import Groq, APIConnectionError, APIStatusError, RateLimitError

from config import GROQ_API_KEY, GROQ_MODEL_NAME, MAX_RETRIES

logger = logging.getLogger(__name__)

class LLMInteractionModule:
    """
    Handles all interactions with the Groq API for generating email content, 
    using the official Groq Python SDK. Prompts are loaded from context.txt.
    """
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model_name = GROQ_MODEL_NAME
        
        # New: Load all prompt components from the external file
        self.prompts = self._load_prompts()
        
        if not self.api_key:
            logger.error("GROQ_API_KEY is missing. LLM module will not function.")
            self.client = None
        elif not self.prompts:
            logger.error("Failed to load prompts from context.txt. LLM module will not function.")
            self.client = None
        else:
            # Initialize the Groq client, which automatically picks up the API key
            self.client = Groq(api_key=self.api_key)

    def _load_prompts(self) -> Dict[str, str]:
        """
        Reads prompt context from src/context.txt and parses it into a dictionary.
        """
        # Determine the path to context.txt (it is in the parent directory of 'modules')
        context_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompt.txt')
        
        if not os.path.exists(context_file_path):
            logger.error(f"Context file not found at: {context_file_path}")
            return {}

        try:
            with open(context_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple parsing using markers defined in context.txt
            sections = content.split('###')
            
            # Map sections to keys (skipping the first empty element)
            prompts = {}
            for section in sections[1:]:
                lines = section.strip().split('\n', 1)
                if len(lines) == 2:
                    key = lines[0].strip()
                    value = lines[1].strip()
                    prompts[key] = value
            
            if 'JSON_FORMAT_DESCRIPTION' not in prompts:
                logger.error("Missing critical 'JSON_FORMAT_DESCRIPTION' in context.txt")
                return {}

            logger.info("Successfully loaded LLM prompts from context.txt.")
            return prompts

        except Exception as e:
            logger.error(f"Error reading or parsing context.txt: {e}")
            return {}


    def _generate_content_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Makes the Groq API call using the SDK with exponential backoff for robustness.
        """
        if not self.client:
            logger.error("Groq client not initialized. Cannot call API.")
            return None
            
        for attempt in range(MAX_RETRIES):
            try:
                # SDK call: unpack messages and response_format from the payload
                response = self.client.chat.completions.create(
                    model=payload['model'],
                    messages=payload['messages'],
                    response_format=payload['response_format'],
                    timeout=30
                )
                
                # Convert the SDK response object to a standard dictionary for consistent parsing
                return response.model_dump()

            # Handle specific Groq SDK exceptions for reliable retries
            except (APIConnectionError, APIStatusError, RateLimitError) as e:
                logger.warning(f"Groq API call attempt {attempt + 1} failed (SDK Error: {type(e).__name__}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Groq API call failed after all retries.")
                    return None
            except Exception as e:
                logger.error(f"An unexpected error occurred during Groq API call: {e}")
                return None
        return None
    
    def generate_consolidated_email(self, data_batch: List[Dict[str, str]]) -> Dict[str, str] | None:
        """
        Generates a SINGLE consolidated email draft summarizing the entire batch of offers.
        """
        if not self.prompts:
            return None
        
        # 1. Prompt Engineering (Constructing the prompts using loaded context)
        
        # The full system instruction combines the core instruction and the JSON format description
        system_instruction = (
            f"{self.prompts['SYSTEM_INSTRUCTION_CORE']} "
            f"{self.prompts['JSON_FORMAT_DESCRIPTION']}"
        )
        
        # The full user prompt combines the core instruction and the dynamic data
        user_prompt = (
            f"{self.prompts['USER_PROMPT_CORE']}\n\n"
            f"Batch data (List of offers):\n{json.dumps(data_batch, indent=2)}"
        )

        # 2. Construct Payload (Groq SDK Format)
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"} 
        }

        # 3. Call API
        logger.info(f"Generating consolidated email content for batch of {len(data_batch)} offers using Groq SDK...")
        api_response = self._generate_content_with_retry(payload)

        if not api_response:
            logger.error(f"Failed to get a consolidated response.")
            return None

        # 4. Extract and Parse Content
        try:
            # SDK response structure: choices[0].message.content
            json_text = api_response['choices'][0]['message']['content']
            email_draft = json.loads(json_text)
            
            # Basic validation
            if 'subject' in email_draft and 'body' in email_draft:
                logger.info(f"Successfully parsed consolidated email draft.")
                return email_draft
            else:
                logger.error(f"Parsed JSON is missing 'subject' or 'body' keys: {email_draft}")
                return None

        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.debug(f"Raw API Response: {api_response}")
            return None