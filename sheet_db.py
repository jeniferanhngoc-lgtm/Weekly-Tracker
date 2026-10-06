import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

def get_history_sheet(secrets):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(secrets["spreadsheet_id"]).worksheet("Tasks_History")
    return sheet

def append_tasks_to_history(secrets, tasks_list):
    sheet = get_history_sheet(secrets)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows_to_add = []
    for t in tasks_list:
        rows_to_add.append([
            t["task_id"],
            t["title"],
            t.get("category", ""),
            t.get("priority", "P2"),
            t.get("deadline", ""),
            str(t.get("subtasks", "")),
            "Pending",
            now_str,
            now_str
        ])
    sheet.append_rows(rows_to_add)

def update_task_status_history(secrets, task_id, new_status):
    sheet = get_history_sheet(secrets)
    cell = sheet.find(str(task_id))
    if cell:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.update_cell(cell.row, 7, new_status)
        sheet.update_cell(cell.row, 9, now_str)
