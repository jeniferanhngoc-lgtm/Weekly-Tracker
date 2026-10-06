import json
import time
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
    
    # Danh sách các mô hình dự phòng theo thứ tự ưu tiên
    candidate_models = ['gemini-3.8-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    
    last_exception = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=raw_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            last_exception = e
            # Nếu gặp lỗi 503 (quá tải), chờ 1 giây rồi thử mô hình tiếp theo
            time.sleep(1)
            continue
            
    # Nếu tất cả các mô hình đều lỗi, báo ngoại lệ cuối cùng
    raise last_exception
