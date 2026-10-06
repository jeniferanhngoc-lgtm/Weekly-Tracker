import datetime
import streamlit as st
import pandas as pd
from sheets_db import load_weekly_sheet, save_weekly_sheet, DAYS, COLUMNS

st.set_page_config(page_title="Weekly Grid Planner", layout="wide")

# Lấy năm và số tuần hiện tại theo ISO Calendar
today = datetime.date.today()
current_year, current_week, _ = today.isocalendar()

st.title("Bảng Quản Lý Công Việc Theo Tuần")

# Thanh chọn Tuần & Năm
col_select1, col_select2 = st.columns([2, 2])
with col_select1:
    selected_year = st.number_input("Năm", min_value=2024, max_value=2030, value=current_year)
with col_select2:
    selected_week = st.number_input("Tuần thứ", min_value=1, max_value=53, value=current_week)

# Xác định ngày T2 và CN của tuần đang chọn
first_day_of_week = datetime.date.fromisocalendar(int(selected_year), int(selected_week), 1)
last_day_of_week = datetime.date.fromisocalendar(int(selected_year), int(selected_week), 7)

st.caption(f"Thời gian: **Thứ 2 ({first_day_of_week.strftime('%d/%m/%Y')})** đến **Chủ Nhật ({last_day_of_week.strftime('%d/%m/%Y')})**")

# Tải dữ liệu của tuần được chọn
week_key = f"df_grid_{selected_year}_{selected_week}"
if week_key not in st.session_state:
    st.session_state[week_key] = load_weekly_sheet(int(selected_year), int(selected_week))

df = st.session_state[week_key]

# Thống kê nhanh
total_tasks = len(df[df["Tên công việc"].str.strip() != ""]) if not df.empty else 0
total_checks = df[DAYS].sum().sum() if total_tasks > 0 else 0
max_checks = total_tasks * 7
overall_percent = (total_checks / max_checks * 100) if max_checks > 0 else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Tổng công việc tuần này", total_tasks)
col2.metric("Số lượt tích hoàn thành", f"{total_checks} / {max_checks}")
col3.metric("Tỷ lệ đạt tuần", f"{overall_percent:.1f}%")

st.progress(overall_percent / 100 if max_checks > 0 else 0.0)
st.divider()

# Cấu hình hiển thị bảng tính
column_config = {
    "Tên công việc": st.column_config.TextColumn("Tên công việc", required=True, width="large"),
    "Mức ưu tiên": st.column_config.SelectboxColumn("Ưu tiên", options=["P1", "P2", "P3"], default="P2", width="small")
}
for day in DAYS:
    column_config[day] = st.column_config.CheckboxColumn(day, default=False, width="small")

st.subheader(f"Bảng Lịch Tuần {selected_week} - Năm {selected_year}")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config=column_config,
    key=f"editor_{selected_year}_{selected_week}"
)

if st.button("Lưu & Đồng bộ Google Sheets", type="primary"):
    clean_df = edited_df[edited_df["Tên công việc"].astype(str).str.strip() != ""].copy()
    save_weekly_sheet(int(selected_year), int(selected_week), clean_df)
    st.session_state[week_key] = clean_df
    st.success(f"Đã lưu tiến độ Tuần {selected_week} ({selected_year}) vào Google Sheets thành công!")
    st.rerun()

st.divider()

# Thống kê chi tiết
if total_tasks > 0:
    st.subheader("Chi tiết chưa đạt trong tuần")
    for _, row in edited_df.iterrows():
        task_name = row["Tên công việc"]
        if task_name and str(task_name).strip():
            unchecked_days = [day for day in DAYS if not row[day]]
            done_count = 7 - len(unchecked_days)
            pct = (done_count / 7) * 100
            
            if unchecked_days:
                st.write(f"- **{task_name}** ({pct:.0f}%): Chưa xong vào {', '.join(unchecked_days)}")
            else:
                st.write(f"- **{task_name}**: Hoàn thành 100% tất cả các ngày!")
