import pandas as pd
import logging
import os
import time
import json
from typing import Dict, Any, Optional, Tuple, List
import gspread
from google.oauth2.service_account import Credentials

from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound 

# NEW IMPORTS: ROW_ID_COLUMN and MAIN_SHEET_NAME are required from config.py
from config import *

logger = logging.getLogger(__name__)


class DataManager:
    """
    Handles all data source reading (from Agent_Queue) and writing (to Main Sheet),
    state management, and row selection, using the gspread library.
    """
    def __init__(self):
        self.sheet_id = SHEET_ID
        self.queue_sheet_name = SHEET_NAME 
        self.main_sheet_name = MAIN_SHEET_NAME 
        self.id_col = ID_COLUMN
        self.status_col = STATUS_COLUMN
        self.score_col = SCORE_COLUMN
        self.letter_col = LETTER_COLUMN
        self.row_id_col = ROW_ID_COLUMN # Absolute row number column (CRITICAL for updates)
        self.cv_col = CV_COLUMN
        
        # Authenticate and get both worksheet objects
        self.main_worksheet: Optional[gspread.Worksheet]
        self.queue_worksheet: Optional[gspread.Worksheet]
        self.main_worksheet, self.queue_worksheet = self._authenticate_and_build_service() 
        self.df = self._load_data()
        self.cv_data = self._load_cv_data()


    def _authenticate_and_build_service(self) -> Tuple[Optional[gspread.Worksheet], Optional[gspread.Worksheet]]:
        """Authenticates and returns the main and queue worksheet objects."""
        try:
            credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            gc = gspread.authorize(credentials)
            spreadsheet = gc.open_by_key(self.sheet_id)
            
            main_ws = spreadsheet.worksheet(self.main_sheet_name)
            queue_ws = spreadsheet.worksheet(self.queue_sheet_name)
            
            logger.info("Successfully connected to Google Sheet and opened main/queue worksheets.")
            return main_ws, queue_ws
            
        except SpreadsheetNotFound:
            logger.critical(f"Spreadsheet not found with ID: {self.sheet_id}")
            return None, None
        except WorksheetNotFound as e:
            logger.critical(f"One or both worksheets not found: {e}")
            return None, None
        except Exception as e:
            logger.critical(f"Authentication or service build failed: {e}")
            return None, None

    def _get_sheet_col_index(self, col_name: str, worksheet: Optional[gspread.Worksheet]) -> Optional[int]:
        """Finds the 1-based column index in the given worksheet."""
        if not worksheet:
            return None
        try:
            # gspread uses the header row to find the index
            col_index = worksheet.find(col_name).col
            return col_index
        # FIX: Catch the correct exception name for a missing cell/column
        except Exception as e: 
            logger.error(f"Column '{col_name}' not found in sheet '{worksheet.title}'.")
            return None
        
        
    def _load_data(self) -> pd.DataFrame:
        """Loads the pre-filtered Agent_Queue sheet into a DataFrame and performs type coercion."""
        if not self.queue_worksheet:
            logger.critical("Cannot load data: Queue worksheet not initialized.")
            return pd.DataFrame()
            
        try:
            # Loads the pre-filtered data (already limited, sorted, and filtered by the Google Sheet QUERY)
            df = pd.DataFrame(self.queue_worksheet.get_all_records())
            if df.empty:
                return pd.DataFrame()

            # --- Type Coercion and Critical Checks ---
            
            # 1. Row ID (CRITICAL for writing back to main sheet)
            
            if self.row_id_col in df.columns:
                 df[self.row_id_col] = pd.to_numeric(df[self.row_id_col], errors='coerce').astype(int)
                 
            else:
                 logger.critical(f"Required column '{self.row_id_col}' (absolute row number) missing from queue data.")
                 return pd.DataFrame() 

            # 2. Other columns
            # df[self.id_col] = pd.to_numeric(df[self.id_col], errors='coerce').fillna(-1).astype(int)
            df[self.score_col] = pd.to_numeric(df[self.score_col], errors='coerce').fillna(0)
            

            logger.info(f"Successfully loaded {len(df)} pre-filtered records from '{self.queue_sheet_name}'.")
            return df
            
        except Exception as e:
            logger.error(f"Data loading failed: {e}")
            return pd.DataFrame()


    def get_pending_batch(self, batch_size: int = BATCH_SIZE) -> list[dict]:
        """
        Loads the pre-filtered sheet (already sorted and limited) and converts 
        it to a list of dicts, ensuring JSON serialization safety.
        """
        # Load the sheet which is already pre-filtered by the Google Sheet QUERY
        self.df = self._load_data() 
        
        if self.df.empty:
            logger.info("No records loaded from the queue sheet.")
            return []

        # The data is already filtered, sorted, and limited by the Google Sheet QUERY.
        batch_df = self.df.copy() 

        

        # Convert the DataFrame slice to a list of dictionaries
        batch_list = batch_df.to_dict('records')
        
        logger.info(f"Prepared {len(batch_list)} records from the queue sheet for processing.")
        return batch_list
        

    def update_status(self, record_id: int, new_status: str):
        """
        Updates the status for a specific row in the original (main) Google Sheet
        using the absolute row number (ROW_ID_COLUMN) retrieved from the queue data.
        """
        # 1. Find the local dataframe row and extract the absolute sheet row number
        try:
            df_row = self.df[self.df[self.id_col] == record_id].iloc[0]
            sheet_row_number = df_row[self.row_id_col] # Row number in the main sheet
        except (IndexError, KeyError):
            logger.warning(f"Could not locate record ID {record_id} in local queue data for update.")
            return

        # 2. Get the column index in the MAIN sheet
        status_col_index = self._get_sheet_col_index(self.status_col, self.main_worksheet)
        
        if status_col_index and self.main_worksheet:
            try:
                # Write back to the ORIGINAL (MAIN) Google Sheet
                self.main_worksheet.update_cell(sheet_row_number, status_col_index, new_status)
                
                logger.info(f"Status for ID {record_id} successfully updated in main sheet to '{new_status}' (Abs Row: {sheet_row_number}).")
            except Exception as e:
                logger.error(f"Failed to update status for ID {record_id} in main sheet: {e}")
        else:
            logger.warning(f"Could not locate status column in main sheet or main worksheet is invalid.")


    def update_motivation_letter(self, record_id: int, letter_content: str):
        """
        Updates the motivation letter content for a specific row in the original (main) Google Sheet.
        """
        # 1. Find the local dataframe row and extract the absolute sheet row number
        try:
            df_row = self.df[self.df[self.id_col] == record_id].iloc[0]
            sheet_row_number = df_row[self.row_id_col] # Row number in the main sheet
        except (IndexError, KeyError):
            logger.warning(f"Could not locate record ID {record_id} in local queue data for letter update.")
            return

        # 2. Get the column index in the MAIN sheet
        letter_col_index = self._get_sheet_col_index(self.letter_col, self.main_worksheet)
        
        if letter_col_index and self.main_worksheet:
            try:
                # Write back to the ORIGINAL (MAIN) Google Sheet
                self.main_worksheet.update_cell(sheet_row_number, letter_col_index, json.dumps(letter_content))
                
                logger.debug(f"Letter content for ID {record_id} successfully updated in main sheet (Abs Row: {sheet_row_number}).")
            except Exception as e:
                logger.error(f"Failed to update letter content for ID {record_id} in main sheet: {e}")
        else:
            logger.warning(f"Could not locate letter column in main sheet or main worksheet is invalid.")


    def _load_cv_data(self) -> Dict[str, Any]:
        """Loads the candidate's CV data from a local JSON file."""
        if self.cv_col in self.df.columns :
            return self.df[self.cv_col][0]
        logger.error(f"can't find the cv column {self.cv_col}")