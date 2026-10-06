import streamlit as st
import pandas as pd
from sheets_db import load_tasks, save_tasks

st.set_page_config(page_title="Weekly Planner", layout="wide")

st.title("Quản lý Công việc Tuần")

if "df_tasks" not in st.session_state:
    st.session_state.df_tasks = load_tasks()

df = st.session_state.df_tasks

total_tasks = len(df)
completed_tasks = int(df["Trạng thái"].sum()) if total_tasks > 0 and "Trạng thái" in df.columns else 0
percent_completed = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
pending_tasks = total_tasks - completed_tasks

col1, col2, col3 = st.columns(3)
col1.metric("Tổng công việc", total_tasks)
col2.metric("Đã hoàn thành", f"{completed_tasks} ({percent_completed:.1f}%)")
col3.metric("Chưa hoàn thành", pending_tasks)

st.divider()

st.subheader("Danh sách công việc")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Trạng thái": st.column_config.CheckboxColumn(
            "Đã xong",
            default=False
        ),
        "Tên công việc": st.column_config.TextColumn(
            "Tên công việc",
            required=True
        ),
        "Ưu tiên": st.column_config.SelectboxColumn(
            "Mức độ ưu tiên",
            options=["P1", "P2", "P3"],
            default="P2"
        )
    }
)

if st.button("Lưu vào Google Sheets", type="primary"):
    save_tasks(edited_df)
    st.session_state.df_tasks = edited_df
    st.success("Đã lưu dữ liệu và cập nhật Google Sheets thành công.")
    st.rerun()

st.divider()

if total_tasks > 0:
    st.subheader("Báo cáo tiến độ")
    st.progress(percent_completed / 100)
    
    if pending_tasks > 0:
        st.write("Các công việc chưa hoàn thành:")
        pending_df = edited_df[~edited_df["Trạng thái"]]
        for _, row in pending_df.iterrows():
            if row["Tên công việc"]:
                st.write(f"- {row['Tên công việc']} (Ưu tiên: {row.get('Ưu tiên', 'N/A')}, Hạn chót: {row.get('Hạn chót', 'N/A')})")
    else:
        st.info("Tất cả công việc trong tuần đã hoàn thành.")
