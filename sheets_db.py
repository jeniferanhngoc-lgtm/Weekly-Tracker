import gspread
import streamlit as st

def append_tasks_to_history(tasks_list):
    # Lấy ID Google Sheet từ Streamlit Secrets
    spreadsheet_id = st.secrets["14Sm3SZhaoV-MOwFuH0C2qNZYN_KB5wKFPpZNh8fq4Y8"]
    
    # Kết nối gspread bằng Google Service Account
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    
    # Mở bảng tính bằng ID (không bọc trong st.secrets[])
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("Tasks_History")
    
    rows_to_add = []
    for task in tasks_list:
        rows_to_add.append([
            task.get("task_id", ""),
            task.get("title", ""),
            task.get("category", ""),
            task.get("priority", ""),
            task.get("deadline", ""),
            ", ".join(task.get("subtasks", [])) if isinstance(task.get("subtasks"), list) else str(task.get("subtasks", ""))
        ])
    
    worksheet.append_rows(rows_to_add)
