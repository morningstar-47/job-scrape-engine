import gspread
import pandas as pd

def write_google_sheet(df: pd.DataFrame, spreadsheet_title: str, credentials_path: str, start_cell: str = 'A1'):
    if df.empty:
        print("⚠️ Le DataFrame fourni est vide. Opération annulée.")
        return False
        
    # 1. Authentification
    gc = gspread.service_account(filename=credentials_path)

    # 2. Ouvrir la feuille de calcul
    sh = gc.open(spreadsheet_title)
    worksheet = sh.sheet1

    # 3. Préparer les données pour gspread
    # Convertir le DataFrame en une liste de listes (y compris les en-têtes)
    # Les en-têtes doivent être la première liste
    data_to_write = [df.columns.tolist()] + df.values.tolist()
    
    # Déterminer la plage à mettre à jour
    rows = len(data_to_write)
    cols = len(data_to_write[0])
    end_col_letter = gspread.utils.rowcol_to_addr(rows, cols)[0] # Obtient la lettre de la dernière colonne
    end_cell = f"{end_col_letter}{rows}"
    
    # Plage complète pour la mise à jour (ex: 'A1:C10')
    range_label = f"{start_cell}:{end_cell}" 
    
    # --- 4. Écriture des Données ---
    # Écrire toutes les données dans la plage spécifiée
    worksheet.update(range_label, data_to_write)
    return True
