import pandas as pd


PRIORITY_SCORE = {
    "Cao": 0,
    "Trung bình": 1,
    "Thấp": 2,
}


def suggest_task_order(df: pd.DataFrame):
    """
    Sắp xếp công việc hoàn toàn local, không dùng API.
    """

    if df is None or df.empty:
        return []

    work_df = df.copy()

    work_df["_id"] = work_df.index

    work_df["Trạng thái"] = (
        work_df["Trạng thái"]
        .fillna(False)
        .astype(bool)
    )

    work_df["_priority"] = (
        work_df["Mức độ ưu tiên"]
        .map(PRIORITY_SCORE)
        .fillna(99)
    )

    work_df["_deadline"] = pd.to_datetime(
        work_df["Deadline"],
        errors="coerce",
        dayfirst=True,
    )

    work_df["_has_no_deadline"] = (
        work_df["_deadline"].isna()
    )

    work_df = work_df.sort_values(
        by=[
            "Trạng thái",
            "_has_no_deadline",
            "_deadline",
            "_priority",
        ],
        ascending=[
            True,
            True,
            True,
            True,
        ],
        kind="stable",
    )

    result = []

    for _, row in work_df.iterrows():

        reasons = []

        if row["Trạng thái"]:
            reasons.append("Công việc đã hoàn thành")

        else:
            if pd.notna(row["_deadline"]):
                reasons.append(
                    "Có deadline "
                    + row["_deadline"].strftime("%d/%m/%Y %H:%M")
                )

            if row["Mức độ ưu tiên"] == "Cao":
                reasons.append("Mức ưu tiên cao")

            elif row["Mức độ ưu tiên"] == "Trung bình":
                reasons.append("Mức ưu tiên trung bình")

            else:
                reasons.append("Mức ưu tiên thấp")

        result.append(
            {
                "id": int(row["_id"]),
                "reason": ", ".join(reasons),
            }
        )

    return result
