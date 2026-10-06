import json
from openai import OpenAI

def analyze_user_notes(raw_text: str, api_key: str):
    # Khởi tạo client kết nối OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    system_instruction = """
    Phân tích đoạn ghi chú tự do thành danh sách các đầu mục công việc.
    Trả về định dạng JSON thuần túy (JSON object) gồm mảng "tasks" chứa các đối tượng:
    - title: Tên công việc
    - category: Phân loại công việc
    - priority: Mức độ ưu tiên (P1/P2/P3)
    - deadline: Ngày hết hạn (định dạng YYYY-MM-DD)
    - subtasks: Danh sách các bước thực hiện nhỏ
    """

    # Danh sách các model Free cực ngon trên OpenRouter
    # 1. google/gemini-2.0-flash-lite-001:free
    # 2. meta-llama/llama-3.3-70b-instruct:free
    # 3. deepseek/deepseek-r1:free
    
    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-lite-001:free",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": raw_text}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
