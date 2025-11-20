import logging
import sys
import os

# --- Path Setup to handle ModuleNotFoundError: No module named 'src' ---
# This ensures Python can find 'src/config.py' and 'src/modules/data_management.py'
# regardless of where main.py is executed from, by adding the project root to sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Corrected Imports (using module names relative to the new path setup)
from config import BATCH_SIZE, ID_COLUMN, CONSOLIDATED_RECIPIENT_EMAIL
from modules.data_management import DataManager
from modules.llm_integration import LLMInteractionModule
from modules.service_integration import SMTPSender, StatusUpdateHandler # NEW IMPORT

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    The central controller of the intelligent agent.
    Implements the core Agent Flow logic for CONSOLIDATED batch processing.
    """
    def __init__(self):
        logger.info("Initializing Agent Orchestrator components...")
        # 1. Initialize Data Management Layer
        self.data_manager = DataManager() 
        
        # 2. Initialize LLM Layer
        self.llm_module = LLMInteractionModule()
        
        # 3. Initialize External Service Integration Layer (NEW)
        self.smtp_sender = SMTPSender()
        self.update_handler = StatusUpdateHandler(self.data_manager) # Pass DM instance
        logger.info("Initialization complete. Components ready.")

    def run_batch(self):
        """
        Executes the main agent flow to process a batch of data, generate ONE email, 
        and update the status of ALL items in that batch.
        """
        logger.info(f"--- Starting Consolidated Agent Run (Batch Size: {BATCH_SIZE}) ---")

        try:
            # 1. Read and Filter (Data & State Management Layer)
            # Retrieve the entire batch of pending offers
            pending_rows = self.data_manager.get_pending_batch(BATCH_SIZE)
            
            if not pending_rows:
                logger.info("No pending rows found. Agent run finished.")
                return

            num_offers = len(pending_rows)
            logger.info(f"Retrieved {num_offers} offers for consolidated processing.")

            # 2. Drafting (Core Agent Orchestration Layer)
            # Call the LLM ONCE with the entire list of data
            email_draft = self.llm_module.generate_consolidated_email(pending_rows)
            
            if not email_draft:
                logger.error(f"Skipping batch. Failed to generate or parse consolidated email draft from LLM.")
                return
            
            logger.info("Successfully drafted consolidated email.")
            logger.debug(f"Subject: {email_draft['subject']}")

            # 3. Sending (External Service Integration Layer)
            recipient = CONSOLIDATED_RECIPIENT_EMAIL
            try:
                # Use the SMTPSender to attempt sending the email
                is_sent = self.smtp_sender.send_email(recipient, email_draft['subject'], email_draft['body'])
                
                # 4. Confirmation & Status Update for ALL rows
                if is_sent:
                    logger.info(f"Consolidated email successfully sent to {recipient}.")
                    # Update status for every single row in the batch using the handler
                    self.update_handler.handle_batch_sent(pending_rows, 'SENT')

                    logger.info(f"Successfully processed and updated status for all {num_offers} offers.")
                else:
                    # If the consolidated email failed to send, mark ALL rows as error
                    error_msg = "SMTP Failure during consolidated batch send. Check SMTP credentials."
                    logger.warning(f"Failed to send consolidated email to {recipient}. Marking all {num_offers} offers as ERROR.")
                    self.update_handler.handle_batch_sent(pending_rows, 'ERROR', error_msg)

            except Exception as e:
                logger.critical(f"Critical error during email send or status update: {e}")
                error_msg = f"Critical SMTP error: {e}"
                # If a critical failure happens, attempt to mark all records as ERROR
                self.update_handler.handle_batch_sent(pending_rows, 'ERROR', error_msg)


        except Exception as e:
            logger.critical(f"A critical error occurred during the batch run: {e}")

        logger.info("--- Agent Run Finished ---")


if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    orchestrator.run_batch()