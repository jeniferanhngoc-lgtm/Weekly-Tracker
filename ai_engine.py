# ai_engine.py
import json
import google.genai as genai
from google.genai import types

def analyze_user_notes(raw_text: str, api_key: str):
    client = genai.Client(api_key=api_key)
    system_instruction = """
    Phân tích đoạn ghi chú tự do thành danh sách các đầu mục công việc.
    Cung cấp đầu ra dạng JSON gồm mảng các đối tượng có cấu trúc:
    - title: Tên công việc
    - category: Phân loại công việc
    - priority: Mức độ ưu tiên (P1/P2/P3)
    - deadline: Ngày hết hạn (định dạng YYYY-MM-DD)
    - subtasks: Khung sườn hoặc các bước thực hiện
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',  # Đảm bảo tên model chính xác
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)
