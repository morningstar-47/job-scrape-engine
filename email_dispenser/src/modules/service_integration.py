import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

# Relative imports from the project structure
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL
from .data_management import DataManager # Used by StatusUpdateHandler

logger = logging.getLogger(__name__)

class SMTPSender:
    """
    Handles secure connection and sending of the consolidated email draft 
    using the configured SMTP server and Python's built-in libraries.
    """
    def __init__(self):
        self.server = SMTP_SERVER
        self.port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.sender = SENDER_EMAIL
        
        logger.info(f"SMTPSender initialized for {self.server}:{self.port}")
        
        if not self.username or self.username == "your-sending-email@example.com":
            logger.warning("SMTP credentials are placeholders. Email sending will likely fail until config is updated.")

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """
        Connects to the SMTP server and sends the email securely.
        
        Args:
            recipient (str): The email address of the consolidated recipient.
            subject (str): The email subject line.
            body (str): The email body (expected to be plain text).

        Returns:
            bool: True if email was sent successfully, False otherwise.
        """
        if not all([self.server, self.port, self.username, self.password, self.sender]):
            logger.error("SMTP credentials incomplete in config. Cannot send email.")
            return False

        # Build the MIME message object
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Determine the connection method based on the port
        if self.port == 465:
            # Use SSL connection directly for port 465
            smtp_class = smtplib.SMTP_SSL
            connection_info = f"SSL/Port 465"
        else:
            # Use standard SMTP and StartTLS for port 587 (or others)
            smtp_class = smtplib.SMTP
            connection_info = f"StartTLS/Port {self.port}"


        try:
            logger.debug(f"Attempting connection via {connection_info}...")
            
            with smtp_class(self.server, self.port) as server:
                
                if self.port != 465:
                    # Only execute EHLO and STARTTLS for standard SMTP connection (e.g., port 587)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                
                # Authenticate and log in
                server.login(self.username, self.password)
                
                # Send the mail
                server.sendmail(self.sender, recipient, msg.as_string())
                
                logger.info(f"Email successfully sent from {self.sender} to {recipient} via {connection_info}.")
                return True

        except smtplib.SMTPAuthenticationError:
            logger.critical("SMTP Authentication Failed. Check username and App Password/Token in src/config.py.")
            return False
        except smtplib.SMTPConnectError as e:
            # This is the error family that WinError 10060 belongs to
            logger.critical(f"SMTP Connection Failed: Check server/port/firewall. Error: {e}")
            return False
        except Exception as e:
            logger.critical(f"An unexpected error occurred during email sending: {e}")
            return False

class StatusUpdateHandler:
    """
    Encapsulates the logic for batch status updates, ensuring all records 
    in a batch are marked consistently after the consolidated email attempt.
    """
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def handle_batch_sent(self, batch_data: List[Dict], status: str, error_message: str = None):
        """
        Updates the status for all records in the batch.
        
        Args:
            batch_data (List[Dict]): The list of records processed in the batch.
            status (str): The new status ('SENT' or 'ERROR').
            error_message (str, optional): An error message if status is 'ERROR'.
        """
        logger.info(f"Handling status update for batch of {len(batch_data)} records, setting status to '{status}'...")
        for row_data in batch_data:
            record_id = row_data[self.data_manager.id_col]
            # Use the DataManager to physically write the status to the sheet
            self.data_manager.update_status(record_id, status, error_message)