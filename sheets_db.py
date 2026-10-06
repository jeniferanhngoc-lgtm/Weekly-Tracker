import gspread
import pandas as pd
import streamlit as st

COLUMNS = ["Tên công việc", "Mức độ ưu tiên", "Deadline", "Trạng thái"]

def load_weekly_sheet(year: int, week: int):
    """Tải danh sách công việc của tuần được chọn từ Google Sheets."""
    try:
        spreadsheet_id = st.secrets["14Sm3SZhaoV-MOwFuH0C2qNZYN_KB5wKFPpZNh8fq4Y8"]
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key(spreadsheet_id)
        
        try:
            worksheet = sh.worksheet("Simple_Weekly_Tasks")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="Simple_Weekly_Tasks", rows="500", cols="10")
            worksheet.append_row(["Năm", "Tuần", "Mốc thời gian"] + COLUMNS)
            return pd.DataFrame(columns=COLUMNS)

        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)
        
        df_all = pd.DataFrame(data)
        df_filtered = df_all[(df_all["Năm"] == year) & (df_all["Tuần"] == week)].copy()
        
        if df_filtered.empty:
            return pd.DataFrame(columns=COLUMNS)
        
        # Đồng bộ dữ liệu cũ (nếu có cột "Đã xong" thì chuyển về "Trạng thái")
        if "Trạng thái" in df_filtered.columns:
            df_filtered["Trạng thái"] = df_filtered["Trạng thái"].apply(
                lambda x: True if str(x).lower() in ["true", "1", "x", "hoàn thành"] else False
            )
        elif "Đã xong" in df_filtered.columns:
            df_filtered["Trạng thái"] = df_filtered["Đã xong"].apply(
                lambda x: True if str(x).lower() in ["true", "1", "x", "hoàn thành"] else False
            )
        else:
            df_filtered["Trạng thái"] = False
            
        return df_filtered[COLUMNS]
    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def save_weekly_sheet(year: int, week: int, time_range_str: str, df_current: pd.DataFrame):
    """Lưu danh sách công việc của tuần vào Google Sheets."""
    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet("Simple_Weekly_Tasks")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title="Simple_Weekly_Tasks", rows="500", cols="10")
        worksheet.append_row(["Năm", "Tuần", "Mốc thời gian"] + COLUMNS)

    data = worksheet.get_all_records()
    if data:
        df_all = pd.DataFrame(data)
        df_other = df_all[~((df_all["Năm"] == year) & (df_all["Tuần"] == week))].copy()
    else:
        df_other = pd.DataFrame(columns=["Năm", "Tuần", "Mốc thời gian"] + COLUMNS)

    df_save = df_current.copy()
    df_save.insert(0, "Năm", year)
    df_save.insert(1, "Tuần", week)
    df_save.insert(2, "Mốc thời gian", time_range_str)

    df_final = pd.concat([df_other, df_save], ignore_index=True)
    
    worksheet.clear()
    data_to_write = [df_final.columns.tolist()] + df_final.values.tolist()
    worksheet.update("A1", data_to_write)
