import pandas as pd


PRIORITY_SCORE = {
    "Cao": 0,
    "Trung bình": 1,
    "Thấp": 2,
}


def suggest_task_order(
    df: pd.DataFrame
):

    """
    Bộ gợi ý local, miễn phí.

    Quy tắc:
    1. Chưa hoàn thành trước
    2. Mức độ ưu tiên:
       Cao > Trung bình > Thấp
    3. Trong cùng mức ưu tiên:
       - có deadline trước
       - deadline gần trước
    4. Task tồn được ưu tiên hơn nếu
       các tiêu chí trên bằng nhau
    5. Task hoàn thành xuống cuối
    """

    if df is None or df.empty:
        return []


    work_df = df.copy()


    work_df["_id"] = (
        work_df.index
    )


    # =====================================================
    # STATUS
    # =====================================================

    work_df["Trạng thái"] = (
        work_df[
            "Trạng thái"
        ]
        .fillna(False)
        .astype(bool)
    )


    # =====================================================
    # PRIORITY
    # =====================================================

    work_df["_priority"] = (
        work_df[
            "Mức độ ưu tiên"
        ]
        .map(
            PRIORITY_SCORE
        )
        .fillna(99)
    )


    # =====================================================
    # DEADLINE
    # =====================================================

    work_df["_deadline"] = (
        pd.to_datetime(
            work_df[
                "Deadline"
            ],
            errors="coerce",
            dayfirst=True,
        )
    )


    work_df[
        "_no_deadline"
    ] = (
        work_df[
            "_deadline"
        ].isna()
    )


    # =====================================================
    # CARRY OVER
    # =====================================================

    if "Nguồn" in work_df.columns:

        work_df[
            "_carryover"
        ] = ~(
            work_df[
                "Nguồn"
            ]
            .astype(str)
            .eq("Tuần này")
        )

    else:

        work_df[
            "_carryover"
        ] = False


    # False sẽ lên trước True,
    # nên đảo carry-over để task tồn
    # đứng trước task thường khi bằng nhau.
    work_df[
        "_carryover_rank"
    ] = ~work_df[
        "_carryover"
    ]


    # =====================================================
    # SORT
    # =====================================================

    work_df = (
        work_df.sort_values(
            by=[
                "Trạng thái",
                "_priority",
                "_no_deadline",
                "_deadline",
                "_carryover_rank",
            ],
            ascending=[
                True,
                True,
                True,
                True,
                True,
            ],
            kind="stable",
        )
    )


    # =====================================================
    # RESULT
    # =====================================================

    result = []


    for _, row in work_df.iterrows():

        reasons = []


        if row[
            "Trạng thái"
        ]:

            reasons.append(
                "Đã hoàn thành"
            )

        else:

            priority = row.get(
                "Mức độ ưu tiên",
                "",
            )


            if priority == "Cao":

                reasons.append(
                    "Ưu tiên cao"
                )

            elif priority == "Trung bình":

                reasons.append(
                    "Ưu tiên trung bình"
                )

            elif priority == "Thấp":

                reasons.append(
                    "Ưu tiên thấp"
                )


            if pd.notna(
                row[
                    "_deadline"
                ]
            ):

                reasons.append(
                    "deadline "
                    + row[
                        "_deadline"
                    ].strftime(
                        "%d/%m/%Y %H:%M"
                    )
                )


            if (
                "Nguồn"
                in work_df.columns
                and
                str(
                    row.get(
                        "Nguồn",
                        "",
                    )
                )
                != "Tuần này"
            ):

                reasons.append(
                    str(
                        row.get(
                            "Nguồn"
                        )
                    )
                )


        result.append(
            {
                "id": int(
                    row["_id"]
                ),

                "reason":
                    ", ".join(
                        reasons
                    ),
            }
        )


    return result
