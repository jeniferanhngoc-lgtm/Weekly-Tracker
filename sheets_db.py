import gspread
import pandas as pd
import streamlit as st

def load_tasks():
    try:
        spreadsheet_id = st.secrets["14Sm3SZhaoV-MOwFuH0C2qNZYN_KB5wKFPpZNh8fq4Y8"]
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key(spreadsheet_id)
        
        try:
            worksheet = sh.worksheet("Weekly_Tasks")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="Weekly_Tasks", rows="100", cols="10")
            worksheet.append_row(["Tên công việc", "Phân loại", "Ưu tiên", "Hạn chót", "Trạng thái"])
            return pd.DataFrame(columns=["Tên công việc", "Phân loại", "Ưu tiên", "Hạn chót", "Trạng thái"])

        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=["Tên công việc", "Phân loại", "Ưu tiên", "Hạn chót", "Trạng thái"])
        
        df = pd.DataFrame(data)
        if "Trạng thái" in df.columns:
            df["Trạng thái"] = df["Trạng thái"].apply(lambda x: True if str(x).lower() in ["true", "1", "hoàn thành", "x"] else False)
        return df
    except Exception:
        return pd.DataFrame(columns=["Tên công việc", "Phân loại", "Ưu tiên", "Hạn chót", "Trạng thái"])

def save_tasks(df):
    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet("Weekly_Tasks")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title="Weekly_Tasks", rows="100", cols="10")

    worksheet.clear()
    
    df_save = df.copy()
    df_save["Hạn chót"] = df_save["Hạn chót"].astype(str)
    
    data_to_write = [df_save.columns.tolist()] + df_save.values.tolist()
    worksheet.update("A1", data_to_write)
