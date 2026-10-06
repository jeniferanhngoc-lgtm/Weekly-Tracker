import uuid
import streamlit as st
from ai_engine import analyze_user_notes
from sheets_db import append_tasks_to_history

st.set_page_config(
    page_title="AI Weekly Planner",
    layout="wide"
)

st.title("AI Weekly Planner & Task Extractor")
st.markdown("Dán đoạn ghi chú hoặc danh sách công việc vào ô bên dưới để AI tự động trích xuất và đồng bộ vào Google Sheets.")

st.divider()

raw_notes = st.text_area(
    label="Ghi chú tuần / Công việc cần làm:",
    height=200,
    placeholder="Ví dụ:\n- Họp nhóm nghiên cứu thiết kế vào 9h sáng mai (P1)\n- Hoàn thành báo cáo tiến độ tuần này trước thứ 6"
)

if st.button("Phân tích ghi chú", type="primary"):
    if not raw_notes.strip():
        st.warning("Vui lòng nhập nội dung ghi chú trước khi phân tích.")
    else:
        with st.spinner("AI đang phân tích và trích xuất danh sách công việc..."):
            try:
                api_key = st.secrets.get("OPENROUTER_API_KEY") or st.secrets.get("GROQ_API_KEY") or st.secrets.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("Không tìm thấy API Key trong Streamlit Secrets!")
                    st.stop()

                parsed = analyze_user_notes(raw_notes, api_key)
                
                if isinstance(parsed, dict) and "tasks" in parsed:
                    tasks_list = parsed["tasks"]
                elif isinstance(parsed, list):
                    tasks_list = parsed
                else:
                    tasks_list = []

                processed_tasks = []
                for item in tasks_list:
                    if isinstance(item, dict):
                        item["task_id"] = f"task_{str(uuid.uuid4())[:6]}"
                        processed_tasks.append(item)

                if processed_tasks:
                    append_tasks_to_history(processed_tasks)
                    st.success(f"Đã phân tích và lưu thành công {len(processed_tasks)} công việc vào Google Sheets!")
                    st.subheader("Công việc đã trích xuất:")
                    st.dataframe(processed_tasks, use_container_width=True)
                else:
                    st.warning("AI không tìm thấy công việc nào hợp lệ trong ghi chú.")

            except Exception as e:
                st.error(f"Xảy ra lỗi trong quá trình xử lý: {str(e)}")
