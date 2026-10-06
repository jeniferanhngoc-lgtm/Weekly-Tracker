import datetime
import streamlit as st
import pandas as pd
from sheets_db import load_weekly_sheet, save_weekly_sheet, COLUMNS

st.set_page_config(page_title="Weekly Task Planner", layout="wide")

today = datetime.date.today()
current_year, current_week, _ = today.isocalendar()

st.title("Quản Lý Công Việc Theo Tuần")

col_select1, col_select2 = st.columns([2, 2])
with col_select1:
    selected_year = st.number_input("Năm", min_value=2024, max_value=2030, value=current_year)
with col_select2:
    selected_week = st.number_input("Tuần thứ", min_value=1, max_value=53, value=current_week)

first_day_of_week = datetime.date.fromisocalendar(int(selected_year), int(selected_week), 1)
last_day_of_week = datetime.date.fromisocalendar(int(selected_year), int(selected_week), 7)

time_range_str = f"{first_day_of_week.strftime('%d/%m/%Y')} - {last_day_of_week.strftime('%d/%m/%Y')}"
st.subheader(f"Tuần {selected_week} ({time_range_str})")

week_key = f"df_simple_{selected_year}_{selected_week}"
if week_key not in st.session_state:
    st.session_state[week_key] = load_weekly_sheet(int(selected_year), int(selected_week))

df = st.session_state[week_key]

total_tasks = len(df[df["Tên công việc"].astype(str).str.strip() != ""]) if not df.empty else 0
completed_tasks = int(df["Trạng thái"].sum()) if total_tasks > 0 and "Trạng thái" in df.columns else 0
pending_tasks = total_tasks - completed_tasks
overall_percent = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Tổng công việc", total_tasks)
col2.metric("Đã hoàn thành", f"{completed_tasks} ({overall_percent:.1f}%)")
col3.metric("Chưa hoàn thành", pending_tasks)

st.progress(overall_percent / 100 if total_tasks > 0 else 0.0)
st.divider()

# Cấu hình các cột, ô Trạng thái được bật checkbox sẵn mặc định là False
column_config = {
    "Tên công việc": st.column_config.TextColumn("Công việc", required=True, width="large"),
    "Mức độ ưu tiên": st.column_config.SelectboxColumn("Mức độ ưu tiên", options=["Cao", "Trung bình", "Thấp"], default="Trung bình", width="medium"),
    "Deadline": st.column_config.TextColumn("Deadline (nếu có)", width="medium"),
    "Trạng thái": st.column_config.CheckboxColumn("Trạng thái", default=False, width="small")
}

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config=column_config,
    key=f"editor_simple_{selected_year}_{selected_week}"
)

if st.button("Lưu & Đồng bộ Google Sheets", type="primary"):
    clean_df = edited_df[edited_df["Tên công việc"].astype(str).str.strip() != ""].copy()
    save_weekly_sheet(int(selected_year), int(selected_week), time_range_str, clean_df)
    st.session_state[week_key] = clean_df
    st.success(f"Đã lưu tiến độ Tuần {selected_week} ({time_range_str}) vào Google Sheets thành công!")
    st.rerun()

st.divider()

if total_tasks > 0:
    st.subheader("Báo cáo danh sách chưa đạt")
    pending_df = edited_df[~edited_df["Trạng thái"]]
    pending_df_clean = pending_df[pending_df["Tên công việc"].astype(str).str.strip() != ""]
    
    if not pending_df_clean.empty:
        st.write("Các công việc chưa hoàn thành trong tuần:")
        for _, row in pending_df_clean.iterrows():
            deadline_str = f" | Deadline: {row['Deadline']}" if row['Deadline'] and str(row['Deadline']).strip() else ""
            st.write(f"- **{row['Tên công việc']}** (Mức độ: {row['Mức độ ưu tiên']}{deadline_str})")
    else:
        st.info("Tất cả công việc trong tuần đã hoàn thành!")
