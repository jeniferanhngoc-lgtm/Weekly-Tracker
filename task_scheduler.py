import pandas as pd


PRIORITY_SCORE = {
    "Cao": 0,
    "Trung bình": 1,
    "Thấp": 2,
}


def suggest_task_order(df: pd.DataFrame):
    """
    Sắp xếp công việc theo:
    1. Chưa hoàn thành trước
    2. Mức độ ưu tiên: Cao > Trung bình > Thấp
    3. Trong cùng mức ưu tiên:
       - Có deadline trước
       - Deadline gần trước
    4. Công việc đã hoàn thành xuống cuối
    """

    if df is None or df.empty:
        return []

    work_df = df.copy()

    # ID gốc để trả về app.py
    work_df["_id"] = work_df.index


    # =====================================================
    # TRẠNG THÁI
    # =====================================================

    work_df["Trạng thái"] = (
        work_df["Trạng thái"]
        .fillna(False)
        .astype(bool)
    )


    # =====================================================
    # MỨC ĐỘ ƯU TIÊN
    # =====================================================

    work_df["_priority"] = (
        work_df["Mức độ ưu tiên"]
        .map(PRIORITY_SCORE)
        .fillna(99)
    )


    # =====================================================
    # DEADLINE
    # =====================================================

    work_df["_deadline"] = pd.to_datetime(
        work_df["Deadline"],
        errors="coerce",
        dayfirst=True,
    )


    # False = có deadline
    # True = không có deadline
    # Khi sort ascending thì có deadline sẽ lên trước
    work_df["_has_no_deadline"] = (
        work_df["_deadline"].isna()
    )


    # =====================================================
    # SORT
    # =====================================================

    work_df = work_df.sort_values(
        by=[
            "Trạng thái",
            "_priority",
            "_has_no_deadline",
            "_deadline",
        ],
        ascending=[
            True,
            True,
            True,
            True,
        ],
        kind="stable",
    )


    # =====================================================
    # TẠO KẾT QUẢ + LÝ DO
    # =====================================================

    result = []


    for _, row in work_df.iterrows():

        reasons = []


        if row["Trạng thái"]:

            reasons.append(
                "Công việc đã hoàn thành"
            )

        else:

            if row["Mức độ ưu tiên"] == "Cao":

                reasons.append(
                    "Mức ưu tiên cao"
                )

            elif row["Mức độ ưu tiên"] == "Trung bình":

                reasons.append(
                    "Mức ưu tiên trung bình"
                )

            elif row["Mức độ ưu tiên"] == "Thấp":

                reasons.append(
                    "Mức ưu tiên thấp"
                )


            if pd.notna(
                row["_deadline"]
            ):

                reasons.append(
                    "deadline "
                    + row["_deadline"].strftime(
                        "%d/%m/%Y %H:%M"
                    )
                )

            else:

                reasons.append(
                    "không có deadline"
                )


        result.append(
            {
                "id": int(
                    row["_id"]
                ),

                "reason": ", ".join(
                    reasons
                ),
            }
        )


    return result
