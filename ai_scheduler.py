import json

import pandas as pd
import streamlit as st
from openai import OpenAI


def suggest_task_order(df: pd.DataFrame):
    """
    Gửi danh sách công việc cho OpenAI và nhận lại
    thứ tự công việc được đề xuất.

    AI chỉ được sắp xếp thứ tự.
    Không được thay đổi nội dung công việc, deadline,
    mức độ ưu tiên hoặc ghi chú.
    """

    if df is None or df.empty:
        return []


    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )


    tasks = []


    for index, row in df.iterrows():

        deadline = ""

        if pd.notna(
            row.get("Deadline")
        ):

            deadline_value = pd.to_datetime(
                row.get("Deadline"),
                errors="coerce",
            )

            if pd.notna(deadline_value):

                deadline = deadline_value.strftime(
                    "%d/%m/%Y %H:%M"
                )


        tasks.append(
            {
                "id": int(index),

                "ten_cong_viec": str(
                    row.get(
                        "Tên công việc",
                        "",
                    )
                ),

                "muc_do_uu_tien": str(
                    row.get(
                        "Mức độ ưu tiên",
                        "",
                    )
                ),

                "deadline": deadline,

                "ghi_chu": str(
                    row.get(
                        "Ghi chú",
                        "",
                    )
                ),

                "trang_thai": bool(
                    row.get(
                        "Trạng thái",
                        False,
                    )
                ),
            }
        )


    system_instruction = """
Bạn là trợ lý hỗ trợ sắp xếp công việc theo tuần.

Mục tiêu:
Sắp xếp thứ tự công việc mà người dùng nên thực hiện trong tuần.

Quy tắc:

1. Chỉ được sắp xếp lại thứ tự công việc.
2. Không được thay đổi tên công việc.
3. Không được thay đổi deadline.
4. Không được thay đổi mức độ ưu tiên.
5. Không được thay đổi ghi chú.
6. Không được tự tạo thêm công việc.
7. Không được tự tạo ngày hoặc giờ.
8. Công việc đã hoàn thành phải nằm cuối danh sách.
9. Deadline gần hơn thường được ưu tiên hơn.
10. Với deadline tương đương, ưu tiên:
    Cao > Trung bình > Thấp.
11. Công việc không có deadline vẫn phải được đánh giá
    dựa trên mức độ ưu tiên và ghi chú.
12. Mỗi công việc phải có một lý do ngắn gọn bằng tiếng Việt.

Chỉ trả về JSON theo đúng cấu trúc được yêu cầu.
"""


    user_input = json.dumps(
        tasks,
        ensure_ascii=False,
        indent=2,
    )


    response = client.responses.create(
        model="gpt-5.6",
        instructions=system_instruction,
        input=user_input,

        text={
            "format": {
                "type": "json_schema",

                "name": "weekly_task_order",

                "strict": True,

                "schema": {
                    "type": "object",

                    "properties": {
                        "tasks": {
                            "type": "array",

                            "items": {
                                "type": "object",

                                "properties": {
                                    "id": {
                                        "type": "integer"
                                    },

                                    "reason": {
                                        "type": "string"
                                    }
                                },

                                "required": [
                                    "id",
                                    "reason",
                                ],

                                "additionalProperties": False,
                            }
                        }
                    },

                    "required": [
                        "tasks"
                    ],

                    "additionalProperties": False,
                }
            }
        },
    )


    result = json.loads(
        response.output_text
    )


    return result["tasks"]
