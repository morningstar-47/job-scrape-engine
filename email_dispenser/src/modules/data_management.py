import pandas as pd
import logging
import os
import time
# --- Updated Imports for gspread Service Account Flow ---
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

# --- FIX: Changed absolute import (src.config) to relative import (..config) ---
from config import SHEET_ID, SHEET_NAME, ID_COLUMN, STATUS_COLUMN, SCORE_COLUMN, BATCH_SIZE, SERVICE_ACCOUNT_FILE, SCOPES

logger = logging.getLogger(__name__)

# No need for TOKEN_FILE or request imports with service account
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

class DataManager:
    """
    Handles all data source reading, state management (status column tracking),
    and row selection for the agent, using the gspread library and Service Account.
    """
    def __init__(self):
        self.sheet_id = SHEET_ID
        self.sheet_name = SHEET_NAME
        self.id_col = ID_COLUMN
        self.status_col = STATUS_COLUMN
        self.score_col = SCORE_COLUMN # NEW: Initialize score column name
        self.worksheet = self._authenticate_and_build_service() # Now returns the worksheet object
        self.df = self._load_data()

    def _authenticate_and_build_service(self):
        """
        Handles authentication using a Service Account JSON file and authorizes gspread.
        Returns the specific Worksheet object.
        """
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.error(f"Service Account file not found at: {SERVICE_ACCOUNT_FILE}")
            logger.error("Please ensure 'sheet_config.json' (or specified file) is placed correctly.")
            return None
        
        try:
            # 1. Load the credentials from the downloaded JSON file
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            # 2. Authorize the gspread client
            client = gspread.authorize(creds)
            
            # 3. Open the Spreadsheet and specific Worksheet
            spreadsheet = client.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet(self.sheet_name)
            
            logger.info("Successfully connected to Google Sheet via Service Account.")
            return worksheet
        except SpreadsheetNotFound:
            logger.critical(f"Spreadsheet not found with ID: {self.sheet_id}. Check ID and sharing permissions.")
            return None
        except WorksheetNotFound:
            logger.critical(f"Worksheet not found with Name: {self.sheet_name}. Check sheet name.")
            return None
        except Exception as e:
            logger.critical(f"Failed to authenticate and build gspread service: {e}")
            return None

    def _load_data(self) -> pd.DataFrame:
        """
        Reads all data from the Google Sheet range using gspread.
        Ensures status and score columns exist and are of the correct type.
        """
        if not self.worksheet:
            return pd.DataFrame()

        for attempt in range(MAX_RETRIES):
            try:
                # DSR Role: Read all data from the sheet
                # Use get_all_values() to get a list of lists
                data = self.worksheet.get_all_values()
                
                if not data:
                    logger.warning("No data found in the specified sheet.")
                    return pd.DataFrame()
                
                # First row is the header
                header = data[0]
                values = data[1:]
                
                df = pd.DataFrame(values, columns=header)
                
                # State Manager Role: Ensure status column exists and is initialized
                if self.status_col not in df.columns:
                    df[self.status_col] = 'PENDING'
                    logger.info(f"Initialized new column '{self.status_col}' with 'PENDING' status locally.")
                
                # NEW: Ensure score column exists and is numeric
                if self.score_col not in df.columns:
                    # If the column is missing, initialize it with a default score of 0
                    df[self.score_col] = 0 
                    logger.warning(f"Initialized missing score column '{self.score_col}' with default value 0.")
                
                # Convert ID column to integer type for consistent lookup
                # gspread returns strings, so we must coerce types carefully
                df[self.id_col] = pd.to_numeric(df[self.id_col], errors='coerce').fillna(-1).astype(int)
                
                # Convert Score column to numeric, errors='coerce' turns non-numeric into NaN, then fill NaN with 0
                df[self.score_col] = pd.to_numeric(df[self.score_col], errors='coerce').fillna(0) # Ensure it's treated as a number
                
                logger.info(f"Successfully loaded {len(df)} records from Google Sheet.")
                return df

            except Exception as e:
                logger.error(f"General Error reading sheet (Attempt {attempt + 1}): {e}")
            
            time.sleep(RETRY_DELAY * (2 ** attempt)) # Exponential backoff

        logger.error("Failed to load data after multiple retries.")
        return pd.DataFrame()


    def get_pending_batch(self, batch_size: int = BATCH_SIZE) -> list[dict]:
        """
        Row Selector Role: Filters for PENDING rows, sorts by score (highest first), 
        and returns a limited batch. Refreshes the data before filtering to catch external updates.
        """
        # Refresh data before filtering to ensure we have the latest status
        self.df = self._load_data() 
        
        if self.df.empty:
            return []

        # Filter for rows that are PENDING
        pending_df = self.df[self.df[self.status_col] == 'PENDING'].copy() # Use .copy() to avoid SettingWithCopyWarning
        
        if pending_df.empty:
            logger.info("No more PENDING rows to process.")
            return []

        # NEW: Sort by score attribute, highest score first (descending=False)
        if self.score_col in pending_df.columns:
            # We sort the PENDING rows by score, with the highest score first
            pending_df = pending_df.sort_values(by=self.score_col, ascending=False)
            logger.debug(f"Pending offers sorted by {self.score_col} (Highest score first).")
        else:
            logger.warning(f"Cannot sort: '{self.score_col}' column is missing or was not loaded correctly. Proceeding without sort.")


        # Limit to the defined batch size (taking the top N after sorting)
        batch_df = pending_df.head(batch_size)
        
        # Convert to a list of dicts (JSON-like structure) for the Orchestrator
        batch_list = batch_df.to_dict('records')
        
        logger.info(f"Selected a batch of {len(batch_list)} PENDING rows.")
        return batch_list

    def update_status(self, record_id: int, new_status: str, error_message: str = None):
        """
        State Manager Role: Updates the status of a specific row in the Google Sheet 
        based on its ID by finding the corresponding row and column index and using gspread.
        """
        if not self.worksheet:
            logger.warning(f"Cannot update status for ID {record_id}. Worksheet is not initialized.")
            return
            
        if self.df.empty:
            logger.warning(f"Cannot update status for ID {record_id}. DataFrame is empty.")
            return

        try:
            # 1. Find the row index in the local DataFrame
            # Note: gspread row index is 1-based, and includes the header row (i.e., data row 1 is sheet row 2)
            df_idx = self.df[self.df[self.id_col] == record_id].index
            
            if df_idx.empty:
                logger.warning(f"ID {record_id} not found in the data frame. Cannot update status.")
                return

            # The actual sheet row number (1-based) is the pandas index + 2 (1 for 1-based, 1 for header)
            sheet_row_number = df_idx[0] + 2 
            
            # 2. Find the status column index (1-based for gspread update)
            # pandas.get_loc returns 0-based index. gspread update_cell needs 1-based column index.
            status_col_index = self.df.columns.get_loc(self.status_col) + 1
            
            # 3. Write back to Google Sheet using row and column index
            self.worksheet.update_cell(sheet_row_number, status_col_index, new_status)

            # 4. Update local DataFrame to reflect the change immediately
            self.df.loc[df_idx, self.status_col] = new_status
            
            logger.info(f"Status for ID {record_id} successfully updated to '{new_status}' in Google Sheet.")

        except Exception as e:
            logger.error(f"Failed to update status for ID {record_id} via gspread: {e}")
            if error_message:
                logger.error(f"Error details: {error_message}")