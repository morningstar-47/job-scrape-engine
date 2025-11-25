import pandas as pd
import logging
import os
import time
import json
from typing import Dict, Any, Optional
# --- Updated Imports for gspread Service Account Flow ---
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

# --- FIX: Changed absolute import (src.config) to relative import (..config) ---
from config import SHEET_ID, SHEET_NAME, ID_COLUMN, STATUS_COLUMN, SCORE_COLUMN, LETTER_COLUMN, BATCH_SIZE, SERVICE_ACCOUNT_FILE, SCOPES,CV_FILE_PATH, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


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
        self.score_col = SCORE_COLUMN
        self.letter_col = LETTER_COLUMN # NEW: Initialize letter column name
        self.worksheet = self._authenticate_and_build_service() 
        self.df = self._load_data()
        self.cv_data = self._load_cv_data()

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

    def _load_cv_data(self) -> Optional[Dict[str, Any]]:
        """
        Reads and parses the content of the cv.json file.
        """
        if not os.path.exists(CV_FILE_PATH):
            logger.warning(f"CV file not found at: {CV_FILE_PATH}. Agent will run without CV context.")
            return None

        for attempt in range(MAX_RETRIES):
            try:
                with open(CV_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info("Successfully loaded CV data from cv.json.")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from CV file: {e}")
                break # Non-recoverable error
            except Exception as e:
                logger.error(f"Error reading CV file (Attempt {attempt + 1}): {e}")
            
            time.sleep(RETRY_DELAY * (2 ** attempt))

        logger.error("Failed to load CV data after multiple retries.")
        return None


    def _load_data(self) -> pd.DataFrame:
        """
        Reads all data from the Google Sheet range using gspread.
        Ensures status, score, and letter columns exist and are of the correct type.
        """
        if not self.worksheet:
            return pd.DataFrame()

        for attempt in range(MAX_RETRIES):
            try:
                # DSR Role: Read all data from the sheet
                data = self.worksheet.get_all_values()
                
                if not data:
                    logger.warning("No data found in the specified sheet.")
                    return pd.DataFrame()
                
                header = data[0]
                values = data[1:]
                
                df = pd.DataFrame(values, columns=header)
                
                # State Manager Role: Ensure necessary columns exist
                if self.status_col not in df.columns:
                    df[self.status_col] = 'PENDING'
                    logger.info(f"Initialized new column '{self.status_col}' with 'PENDING' status locally.")
                
                if self.score_col not in df.columns:
                    df[self.score_col] = 0 
                    logger.warning(f"Initialized missing score column '{self.score_col}' with default value 0.")
                
                # NEW: Ensure letter column exists
                if self.letter_col not in df.columns:
                    df[self.letter_col] = ''
                    logger.warning(f"Initialized missing letter column '{self.letter_col}' with empty string.")


                # Type Coercion
                df[self.id_col] = pd.to_numeric(df[self.id_col], errors='coerce').fillna(-1).astype(int)
                df[self.score_col] = pd.to_numeric(df[self.score_col], errors='coerce').fillna(0)
                
                logger.info(f"Successfully loaded {len(df)} records from Google Sheet.")
                return df

            except Exception as e:
                logger.error(f"General Error reading sheet (Attempt {attempt + 1}): {e}")
            
            time.sleep(RETRY_DELAY * (2 ** attempt))

        logger.error("Failed to load data after multiple retries.")
        return pd.DataFrame()


    def get_pending_batch(self, batch_size: int = BATCH_SIZE) -> list[dict]:
        """
        Filters for PENDING rows, sorts by score (highest first), 
        and returns a limited batch. Refreshes the data before filtering.
        """
        # Refresh data before filtering
        self.df = self._load_data() 
        
        if self.df.empty:
            return []

        # Filter for rows that are PENDING and have a score > 0 (assuming score = 0 means not yet assessed/relevant)
        # We ensure score > 0 before proceeding to LLM generation
        pending_df = self.df[(self.df[self.status_col] == 'PENDING') & (self.df[self.score_col] > 0)].copy()
        
        if pending_df.empty:
            logger.info("No more PENDING rows with score > 0 to process.")
            return []

        # Sort by score attribute, highest score first
        if self.score_col in pending_df.columns:
            pending_df = pending_df.sort_values(by=self.score_col, ascending=False)
        
        # Limit to the defined batch size
        batch_df = pending_df.head(batch_size)
        
        batch_list = batch_df.to_dict('records')
        
        logger.info(f"Selected a batch of {len(batch_list)} PENDING and scored offers.")
        return batch_list


    def _get_sheet_row_and_col_index(self, record_id: int, column_name: str) -> Optional[tuple[int, int]]:
        """Helper to find the 1-based sheet row and column index for an update."""
        if self.df.empty:
            return None
        
        df_idx = self.df[self.df[self.id_col] == record_id].index
        
        if df_idx.empty:
            logger.warning(f"ID {record_id} not found in the data frame.")
            return None

        # The actual sheet row number (1-based) is the pandas index + 2 (1 for 1-based, 1 for header)
        sheet_row_number = df_idx[0] + 2 
        
        # Find the column index (1-based for gspread update)
        try:
            col_index = self.df.columns.get_loc(column_name) + 1
        except KeyError:
            logger.error(f"Column '{column_name}' not found in the DataFrame columns.")
            return None

        return sheet_row_number, col_index

    def update_motivation_letter(self,record_id:int,motivation_letter : dict[str,any]):
        """
        add the motivation letter for every offer
        """
        indices = self._get_sheet_row_and_col_index(record_id, self.letter_col)
        if indices and self.worksheet:
            sheet_row_number, status_col_index = indices
            try:
                # Write back to Google Sheet
                self.worksheet.update_cell(sheet_row_number, status_col_index, f"{motivation_letter['subject']} : {motivation_letter['body']}")

                # Update local DataFrame
                df_idx = self.df[self.df[self.id_col] == record_id].index[0]
                self.df.loc[df_idx, self.status_col] = f"{motivation_letter['subject']} : {motivation_letter['body']}"
                
                logger.info(f"motivation letter for ID {record_id} successfully updated.")
            except Exception as e:
                logger.error(f"Failed to update status for ID {record_id} via gspread: {e}")
        else:
            logger.warning(f"Could not locate indices for status update of ID {record_id}.")

    def update_status(self, record_id: int, new_status: str):
        """
        Updates the status of a specific row in the Google Sheet.
        """
        indices = self._get_sheet_row_and_col_index(record_id, self.status_col)
        
        if indices and self.worksheet:
            sheet_row_number, status_col_index = indices
            try:
                # Write back to Google Sheet
                self.worksheet.update_cell(sheet_row_number, status_col_index, new_status)

                # Update local DataFrame
                df_idx = self.df[self.df[self.id_col] == record_id].index[0]
                self.df.loc[df_idx, self.status_col] = new_status
                
                logger.info(f"Status for ID {record_id} successfully updated to '{new_status}'.")
            except Exception as e:
                logger.error(f"Failed to update status for ID {record_id} via gspread: {e}")
        else:
            logger.warning(f"Could not locate indices for status update of ID {record_id}.")

    
    def update_letter_content(self, record_id: int, letter_content: str):
        """
        NEW: Updates the motivation letter content for a specific row in the Google Sheet.
        """
        indices = self._get_sheet_row_and_col_index(record_id, self.letter_col)
        
        if indices and self.worksheet:
            sheet_row_number, letter_col_index = indices
            try:
                # Write back to Google Sheet
                self.worksheet.update_cell(sheet_row_number, letter_col_index, letter_content)

                # Update local DataFrame
                df_idx = self.df[self.df[self.id_col] == record_id].index[0]
                self.df.loc[df_idx, self.letter_col] = letter_content
                
                logger.debug(f"Letter content for ID {record_id} successfully updated.")
            except Exception as e:
                logger.error(f"Failed to update letter content for ID {record_id} via gspread: {e}")
        else:
            logger.warning(f"Could not locate indices for letter content update of ID {record_id}.")