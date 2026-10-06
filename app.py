from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from sheets_db import load_week_tasks, save_week_tasks

st.set_page_config(page_title="Weekly Task Sheet", layout="wide")

st.title("Quản lý Công việc theo Tuần")

# 1. Chọn ngày để xác định Tuần (Thứ 2 -> Chủ Nhật)
selected_date = st.date_input("Chọn một ngày trong tuần cần quản lý:", datetime.today())

# Tính ngày Thứ 2 và Chủ Nhật của tuần tương ứng
monday = selected_date - timedelta(days=selected_date.weekday())
sunday = monday + timedelta(days=6)

sheet_name = f"Week_{monday.strftime('%Y%m%d')}"
st.subheader(f"Bảng công việc Tuần: {monday.strftime('%d/%m/%Y')} – {sunday.strftime('%d/%m/%Y')}")

# 2. Tải dữ liệu công việc của tuần được chọn
if "current_sheet" not in st.session_state or st.session_state.current_sheet != sheet_name:
    st.session_state.current_sheet = sheet_name
    st.session_state.df_tasks = load_week_tasks(sheet_name)

df = st.session_state.df_tasks

# 3. Tính toán số liệu tổng hợp
total_tasks = len(df[df["Tên công việc"].astype(str).str.strip() != ""])
completed_tasks = int(df[df["Tên công việc"].astype(str).str.strip() != ""]["Hoàn thành"].sum()) if total_tasks > 0 else 0
percent_completed = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
pending_tasks = total_tasks - completed_tasks

col1, col2, col3 = st.columns(3)
col1.metric("Tổng số công việc", total_tasks)
col2.metric("Đã hoàn thành", f"{completed_tasks} ({percent_completed:.1f}%)")
col3.metric("Chưa hoàn thành", pending_tasks)

st.divider()

# 4. Bảng tính tương tác dạng Sheet
st.markdown("Nhập trực tiếp danh sách công việc vào bảng bên dưới:")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Hoàn thành": st.column_config.CheckboxColumn(
            "Đã xong",
            default=False
        ),
        "Tên công việc": st.column_config.TextColumn(
            "Tên công việc",
            required=True
        ),
        "Mức ưu tiên": st.column_config.SelectboxColumn(
            "Mức ưu tiên",
            options=["P1", "P2", "P3"],
            default="P2"
        ),
        "Hạn chót": st.column_config.DateColumn(
            "Hạn chót",
            min_value=monday,
            max_value=sunday,
            format="YYYY-MM-DD"
        )
    }
)

if st.button("Lưu thay đổi vào Google Sheets", type="primary"):
    save_week_tasks(sheet_name, edited_df)
    st.session_state.df_tasks = edited_df
    st.success(f"Đã lưu thành công dữ liệu cho tuần {monday.strftime('%d/%m/%Y')} – {sunday.strftime('%d/%m/%Y')}!")
    st.rerun()

st.divider()

# 5. Báo cáo đánh giá tiến độ
if total_tasks > 0:
    st.subheader("Báo cáo tiến độ hoàn thành tuần")
    st.progress(percent_completed / 100)
    
    if pending_tasks > 0:
        st.write("Các mục chưa đạt được:")
        pending_df = edited_df[(edited_df["Tên công việc"].astype(str).str.strip() != "") & (~edited_df["Hoàn thành"])]
        for _, row in pending_df.iterrows():
            st.write(f"- **{row['Tên công việc']}** (Mức ưu tiên: {row.get('Mức ưu tiên', 'N/A')}, Hạn chót: {row.get('Hạn chót', 'N/A')})")
    else:
        st.info("Tất cả công việc trong tuần đã hoàn thành xuất sắc!")
