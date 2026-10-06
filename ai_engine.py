import json
import re
from openai import OpenAI, NotFoundError

def clean_and_parse_json(text: str) -> dict:
    """Trích xuất và parse chuỗi JSON từ phản hồi của AI."""
    # Loại bỏ thẻ markdown codeblock nếu AI trả về dạng ```json ... ```
    cleaned_text = re.sub(r'```json\s*', '', text)
    cleaned_text = re.sub(r'```\s*', '', cleaned_text)
    
    match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(cleaned_text.strip())

def analyze_user_notes(raw_text: str, api_key: str):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    system_instruction = """
    Phân tích đoạn ghi chú tự do thành danh sách các đầu mục công việc.
    CHỈ trả về duy nhất 1 chuỗi JSON theo cấu trúc:
    {
      "tasks": [
        {
          "title": "Tên công việc",
          "category": "Phân loại",
          "priority": "P1/P2/P3",
          "deadline": "YYYY-MM-DD",
          "subtasks": ["Bước 1", "Bước 2"]
        }
      ]
    }
    """

    # openrouter/auto sẽ tự chọn mô hình tốt nhất và đang hoạt động cho bạn
    candidate_models = [
        "openrouter/auto",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "google/gemini-2.0-flash-exp:free"
    ]

    last_exception = None
    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": raw_text}
                ]
            )
            content = response.choices[0].message.content
            if content:
                return clean_and_parse_json(content)
        except (NotFoundError, Exception) as e:
            last_exception = e
            continue

    raise last_exception
