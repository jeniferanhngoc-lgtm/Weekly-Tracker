import json
import time
import google.genai as genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

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
    
    # gemini-3.8-flash là mô hình chính thức được Google AI khuyến nghị
    candidate_models = ['gemini-3.8-flash', 'gemini-2.0-flash']
    
    last_exception = None
    for model_name in candidate_models:
        # Thử tối đa 3 lần cho mỗi model
        for attempt in range(3):
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
            except ServerError as e:
                # Nếu gặp lỗi quá tải server (503/500), chờ tăng dần (2s, 4s, 6s) rồi thử lại
                last_exception = e
                time.sleep(2 * (attempt + 1))
                continue
            except ClientError as e:
                # Nếu gặp lỗi Client (404/400), bỏ qua model này và thử model tiếp theo ngay lập tức
                last_exception = e
                break
            except Exception as e:
                last_exception = e
                time.sleep(1)
                continue
            
    raise last_exception
