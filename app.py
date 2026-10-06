import streamlit as st
import pandas as pd
import uuid
from ai_engine import analyze_user_notes
from sheets_db import append_tasks_to_history, update_task_status_history

st.set_page_config(page_title="Personal Planner", layout="wide")

if "web_tasks" not in st.session_state:
    st.session_state["web_tasks"] = []

st.title("Personal Planner")

st.subheader("1. Nhập ghi chú tự do")
raw_notes = st.text_area("Ghi chú công việc", height=100)

if st.button("Phân tích Kế hoạch"):
    if raw_notes:
        parsed = analyze_user_notes(raw_notes, st.secrets["GEMINI_API_KEY"])
        for item in parsed:
            item["task_id"] = f"task_{str(uuid.uuid4())[:6]}"
            item["is_done"] = False
        st.session_state["preview_tasks"] = parsed

if "preview_tasks" in st.session_state and st.session_state["preview_tasks"]:
    st.subheader("2. Xem trước và chỉnh sửa")
    df_preview = pd.DataFrame(st.session_state["preview_tasks"])
    edited_df = st.data_editor(
        df_preview,
        column_config={
            "task_id": None,
            "is_done": None,
            "title": "Tên công việc",
            "category": "Phân loại",
            "priority": "Ưu tiên",
            "deadline": "Hạn chót",
            "subtasks": "Ghi chú"
        },
        num_rows="dynamic",
        use_container_width=True,
        key="preview_editor"
    )

    if st.button("Xác nhận và Lưu"):
        confirmed_tasks = edited_df.to_dict(orient="records")
        st.session_state["web_tasks"].extend(confirmed_tasks)
        try:
            append_tasks_to_history(st.secrets, confirmed_tasks)
        except Exception:
            pass
        del st.session_state["preview_tasks"]
        st.rerun()

st.subheader("3. Danh sách Công việc")
if st.session_state["web_tasks"]:
    total = len(st.session_state["web_tasks"])
    done_count = sum(1 for t in st.session_state["web_tasks"] if t.get("is_done", False))
    efficiency = (done_count / total * 100) if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số việc", total)
    c2.metric("Đã hoàn thành", done_count)
    c3.metric("Hiệu suất", f"{efficiency:.1f}%")
    st.progress(efficiency / 100)

    for idx, task in enumerate(st.session_state["web_tasks"]):
        col_chk, col_content, col_info = st.columns([0.08, 0.72, 0.20])
        
        with col_chk:
            checked = st.checkbox("", value=task.get("is_done", False), key=f"chk_{task['task_id']}")
            if checked != task.get("is_done", False):
                st.session_state["web_tasks"][idx]["is_done"] = checked
                new_status = "Completed" if checked else "Pending"
                try:
                    update_task_status_history(st.secrets, task["task_id"], new_status)
                except Exception:
                    pass
                st.rerun()

        with col_content:
            title_text = f"~~{task['title']}~~" if task.get("is_done") else f"**{task['title']}**"
            st.markdown(f"{title_text} | `{task.get('category', '')}` | Ưu tiên: **{task.get('priority', '')}**")
            if task.get("subtasks"):
                with st.expander("Chi tiết"):
                    st.write(task["subtasks"])

        with col_info:
            st.caption(f"Hạn: {task.get('deadline', '')}")
