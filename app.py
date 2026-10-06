import uuid
import streamlit as st
from ai_engine import analyze_user_notes
from sheets_db import append_tasks_to_history

# ... (các đoạn code khởi tạo giao diện trước đó) ...

if st.button("Phân tích ghi chú"):
    if raw_notes.strip():
        with st.spinner("AI đang trích xuất công việc..."):
            parsed = analyze_user_notes(raw_notes, st.secrets["OPENROUTER_API_KEY"])
            
            # 1. Trích xuất đúng danh sách tasks từ Dictionary hoặc List
            if isinstance(parsed, dict) and "tasks" in parsed:
                tasks_list = parsed["tasks"]
            elif isinstance(parsed, list):
                tasks_list = parsed
            else:
                tasks_list = []

            # 2. Duyệt qua từng công việc và gán task_id
            processed_tasks = []
            for item in tasks_list:
                if isinstance(item, dict):
                    item["task_id"] = f"task_{str(uuid.uuid4())[:6]}"
                    processed_tasks.append(item)

            # 3. Lưu vào Google Sheets và hiển thị ra màn hình
            if processed_tasks:
                append_tasks_to_history(processed_tasks)
                st.success(f"Đã thêm thành công {len(processed_tasks)} công việc vào Google Sheets!")
                st.json(processed_tasks)
            else:
                st.warning("Không tìm thấy công việc nào hợp lệ từ ghi chú.")
