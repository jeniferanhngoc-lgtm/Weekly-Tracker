import streamlit as st
import pandas as pd
from sheets_db import load_weekly_sheet, save_weekly_sheet, DAYS, COLUMNS

st.set_page_config(page_title="Weekly Grid Planner", layout="wide")

st.title("Bảng Quản Lý Công Việc Theo Tuần (Thứ 2 - Chủ Nhật)")

if "df_grid" not in st.session_state:
    st.session_state.df_grid = load_weekly_sheet()

df = st.session_state.df_grid

# Tạo cột cấu hình checkbox cho từng ngày trong tuần
column_config = {
    "Tên công việc": st.column_config.TextColumn("Tên công việc", required=True, width="large"),
    "Mức ưu tiên": st.column_config.SelectboxColumn("Ưu tiên", options=["P1", "P2", "P3"], default="P2", width="small")
}

for day in DAYS:
    column_config[day] = st.column_config.CheckboxColumn(day, default=False, width="small")

# Tính toán thống kê tổng quan
total_tasks = len(df[df["Tên công việc"].str.strip() != ""]) if not df.empty else 0
total_checks = df[DAYS].sum().sum() if total_tasks > 0 else 0
max_checks = total_tasks * 7
overall_percent = (total_checks / max_checks * 100) if max_checks > 0 else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Tổng công việc", total_tasks)
col2.metric("Số lượt tích hoàn thành", f"{total_checks} / {max_checks}")
col3.metric("Tỷ lệ đạt tuần", f"{overall_percent:.1f}%")

st.progress(overall_percent / 100 if max_checks > 0 else 0.0)
st.divider()

st.subheader("Bảng Lịch Tuần")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config=column_config
)

if st.button("Lưu & Đồng bộ Google Sheets", type="primary"):
    # Lọc bỏ các dòng trống
    clean_df = edited_df[edited_df["Tên công việc"].astype(str).str.strip() != ""].copy()
    save_weekly_sheet(clean_df)
    st.session_state.df_grid = clean_df
    st.success("Đã lưu bảng tiến độ tuần vào Google Sheets thành công!")
    st.rerun()

st.divider()

# Thống kê chi tiết các việc chưa hoàn thành trong tuần
if total_tasks > 0:
    st.subheader("Tổng hợp các ngày chưa đạt theo đầu việc")
    for _, row in edited_df.iterrows():
        task_name = row["Tên công việc"]
        if task_name and str(task_name).strip():
            unchecked_days = [day for day in DAYS if not row[day]]
            done_count = 7 - len(unchecked_days)
            pct = (done_count / 7) * 100
            
            if unchecked_days:
                st.write(f"- **{task_name}** ({pct:.0f}%): Chưa xong vào {', '.join(unchecked_days)}")
            else:
                st.write(f"- **{task_name}**: Đạt 100% tất cả các ngày trong tuần!")
