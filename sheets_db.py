import gspread
import pandas as pd
import streamlit as st

# Các cột cần lấy để hiển thị trên giao diện bảng
COLUMNS = ["Tên công việc", "Mức độ ưu tiên", "Deadline", "Trạng thái"]

def load_weekly_sheet(year: int, week: int):
    """Tải danh sách công việc của tuần được chọn từ Google Sheets."""
    try:
        spreadsheet_id = st.secrets["spreadsheet_id"]
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
        
        # Đảm bảo ép kiểu dữ liệu Năm và Tuần về int để so sánh chính xác
        df_all["Năm"] = pd.to_numeric(df_all["Năm"], errors="coerce")
        df_all["Tuần"] = pd.to_numeric(df_all["Tuần"], errors="coerce")
        
        df_filtered = df_all[(df_all["Năm"] == year) & (df_all["Tuần"] == week)].copy()
        
        if df_filtered.empty:
            return pd.DataFrame(columns=COLUMNS)
        
        # Ép kiểu dữ liệu boolean cho cột Trạng thái (checkbox)
        if "Trạng thái" in df_filtered.columns:
            df_filtered["Trạng thái"] = df_filtered["Trạng thái"].apply(
                lambda x: True if str(x).upper() in ["TRUE", "1", "X", "HOÀN THÀNH"] else False
            )
        else:
            df_filtered["Trạng thái"] = False
            
        return df_filtered[COLUMNS]

    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {str(e)}")
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
        # Loại bỏ các dòng cũ của tuần/năm này để ghi đè dữ liệu mới
        df_all["Năm"] = pd.to_numeric(df_all["Năm"], errors="coerce")
        df_all["Tuần"] = pd.to_numeric(df_all["Tuần"], errors="coerce")
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
