import gspread
import pandas as pd
import streamlit as st

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
COLUMNS = ["Tên công việc", "Mức ưu tiên"] + DAYS

def load_weekly_sheet(year: int, week: int):
    """Tải dữ liệu của một tuần cụ thể từ Google Sheets."""
    try:
        spreadsheet_id = st.secrets["spreadsheet_id"]
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key(spreadsheet_id)
        
        try:
            worksheet = sh.worksheet("Weekly_Grid_History")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="Weekly_Grid_History", rows="500", cols="15")
            worksheet.append_row(["Năm", "Tuần"] + COLUMNS + ["% Hoàn thành"])
            return pd.DataFrame(columns=COLUMNS)

        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)
        
        df_all = pd.DataFrame(data)
        
        # Lọc đúng dữ liệu của Năm và Tuần được chọn
        df_filtered = df_all[(df_all["Năm"] == year) & (df_all["Tuần"] == week)].copy()
        
        if df_filtered.empty:
            return pd.DataFrame(columns=COLUMNS)
        
        for day in DAYS:
            if day in df_filtered.columns:
                df_filtered[day] = df_filtered[day].apply(
                    lambda x: True if str(x).lower() in ["true", "1", "x", "hoàn thành"] else False
                )
            else:
                df_filtered[day] = False
                
        return df_filtered[COLUMNS]
    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def save_weekly_sheet(year: int, week: int, df_current: pd.DataFrame):
    """Cập nhật hoặc thêm mới dữ liệu của tuần được chọn vào Google Sheets."""
    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet("Weekly_Grid_History")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title="Weekly_Grid_History", rows="500", cols="15")
        worksheet.append_row(["Năm", "Tuần"] + COLUMNS + ["% Hoàn thành"])

    data = worksheet.get_all_records()
    if data:
        df_all = pd.DataFrame(data)
        # Xóa dữ liệu cũ của tuần này để ghi đè bản mới nhất
        df_other = df_all[~((df_all["Năm"] == year) & (df_all["Tuần"] == week))].copy()
    else:
        df_other = pd.DataFrame(columns=["Năm", "Tuần"] + COLUMNS + ["% Hoàn thành"])

    # Chuẩn bị dữ liệu tuần hiện tại
    df_save = df_current.copy()
    df_save.insert(0, "Năm", year)
    df_save.insert(1, "Tuần", week)
    
    # Tính % hoàn thành từng công việc
    days_checked = df_save[DAYS].sum(axis=1)
    df_save["% Hoàn thành"] = days_checked.apply(lambda x: f"{(x / 7 * 100):.1f}%" if x > 0 else "0.0%")

    # Gộp dữ liệu tuần này với lịch sử các tuần khác
    df_final = pd.concat([df_other, df_save], ignore_index=True)
    
    worksheet.clear()
    data_to_write = [df_final.columns.tolist()] + df_final.values.tolist()
    worksheet.update("A1", data_to_write)
