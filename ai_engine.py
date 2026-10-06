import json
import time
import google.genai as genai
from google.genai import types
from google.genai.errors import APIError

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
    
    # Chỉ sử dụng các model được hỗ trợ chính thức trong SDK google-genai
    candidate_models = ['gemini-2.5-flash', 'gemini-2.0-flash']
    
    last_exception = None
    for model_name in candidate_models:
        # Thử lại tối đa 2 lần cho mỗi model nếu gặp lỗi quá tải (503/429)
        for attempt in range(2):
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
            except APIError as e:
                last_exception = e
                # Nếu là lỗi quá tải (503) hoặc chạm giới hạn (429), tạm dừng 2 giây rồi thử lại
                if e.code in [503, 429]:
                    time.sleep(2)
                    continue
                # Nếu gặp lỗi khác (như 404), chuyển ngay sang model tiếp theo
                break
            except Exception as e:
                last_exception = e
                break
            
    raise last_exception
