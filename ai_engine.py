import json
import re
from openai import OpenAI

def clean_and_parse_json(text: str) -> dict:
    """Hàm bóc tách JSON chuẩn từ phản hồi của AI."""
    # Tìm đoạn chứa JSON trong cặp dấu { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)

def analyze_user_notes(raw_text: str, api_key: str):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    system_instruction = """
    Phân tích đoạn ghi chú tự do thành danh sách các đầu mục công việc.
    CHỈ trả về duy nhất 1 chuỗi JSON (không kèm lời giải thích, không dùng markdown codeblock) theo cấu trúc:
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

    # Danh sách các model Free hoạt động ổn định nhất trên OpenRouter
    candidate_models = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "deepseek/deepseek-r1:free"
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
            return clean_and_parse_json(content)
        except Exception as e:
            last_exception = e
            continue

    raise last_exception
