import gspread
import pandas as pd
import streamlit as st

def get_worksheet(sheet_name):
    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(spreadsheet_id)
    
    try:
        return sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # Tạo sheet mới nếu chưa tồn tại cho tuần đó
        ws = sh.add_worksheet(title=sheet_name, rows="100", cols="10")
        ws.append_row(["Tên công việc", "Phân loại", "Mức ưu tiên", "Hạn chót", "Hoàn thành"])
        return ws

def load_week_tasks(sheet_name):
    try:
        ws = get_worksheet(sheet_name)
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["Tên công việc", "Phân loại", "Mức ưu tiên", "Hạn chót", "Hoàn thành"])
        
        df = pd.DataFrame(data)
        if "Hoàn thành" in df.columns:
            df["Hoàn thành"] = df["Hoàn thành"].apply(lambda x: True if str(x).lower() in ["true", "1", "x", "hoàn thành"] else False)
        return df
    except Exception:
        return pd.DataFrame(columns=["Tên công việc", "Phân loại", "Mức ưu tiên", "Hạn chót", "Hoàn thành"])

def save_week_tasks(sheet_name, df):
    ws = get_worksheet(sheet_name)
    ws.clear()
    
    df_save = df.copy()
    df_save["Hạn chót"] = df_save["Hạn chót"].astype(str)
    
    data_to_write = [df_save.columns.tolist()] + df_save.values.tolist()
    ws.update("A1", data_to_write)
