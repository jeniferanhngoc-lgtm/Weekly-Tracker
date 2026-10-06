import gspread
import pandas as pd
import streamlit as st

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
COLUMNS = ["Tên công việc", "Mức ưu tiên"] + DAYS

def load_weekly_sheet():
    try:
        spreadsheet_id = st.secrets["spreadsheet_id"]
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key(spreadsheet_id)
        
        try:
            worksheet = sh.worksheet("Weekly_Grid")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="Weekly_Grid", rows="50", cols="15")
            worksheet.append_row(COLUMNS)
            return pd.DataFrame(columns=COLUMNS)

        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)
        
        df = pd.DataFrame(data)
        # Chuyển dữ liệu các ngày về kiểu boolean cho checkbox
        for day in DAYS:
            if day in df.columns:
                df[day] = df[day].apply(lambda x: True if str(x).lower() in ["true", "1", "x", "hoàn thành"] else False)
            else:
                df[day] = False
                
        return df[COLUMNS]
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

def save_weekly_sheet(df):
    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet("Weekly_Grid")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title="Weekly_Grid", rows="50", cols="15")

    worksheet.clear()
    
    df_save = df.copy()
    
    # Tính cột tổng hợp tỷ lệ hoàn thành cho từng dòng công việc
    days_checked = df_save[DAYS].sum(axis=1)
    # Nếu dòng đó có đánh dấu checkbox ngày nào thì tính %
    df_save["% Hoàn thành"] = days_checked.apply(lambda x: f"{(x / 7 * 100):.1f}%" if x > 0 else "0.0%")
    
    data_to_write = [df_save.columns.tolist()] + df_save.values.tolist()
    worksheet.update("A1", data_to_write)
