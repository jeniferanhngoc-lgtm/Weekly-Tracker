import datetime

import pandas as pd
import streamlit as st

from sheets_db import (
    COLUMNS,
    load_weekly_sheet,
    save_weekly_sheet,
)

from ai_scheduler import suggest_task_order


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Weekly Task Planner",
    page_icon="📅",
    layout="wide",
)

st.title("Quản Lý Công Việc Theo Tuần")


# =========================================================
# CURRENT DATE / WEEK
# =========================================================

today = datetime.date.today()
current_year, current_week, _ = today.isocalendar()


# =========================================================
# SELECT YEAR / WEEK
# =========================================================

col_select1, col_select2 = st.columns(2)

with col_select1:
    selected_year = st.number_input(
        "Năm",
        min_value=2024,
        max_value=2035,
        value=int(current_year),
        step=1,
    )

with col_select2:
    selected_week = st.number_input(
        "Tuần thứ",
        min_value=1,
        max_value=53,
        value=int(current_week),
        step=1,
    )


selected_year = int(selected_year)
selected_week = int(selected_week)


# =========================================================
# WEEK DATE RANGE
# =========================================================

try:
    first_day_of_week = datetime.date.fromisocalendar(
        selected_year,
        selected_week,
        1,
    )

    last_day_of_week = datetime.date.fromisocalendar(
        selected_year,
        selected_week,
        7,
    )

except ValueError:
    st.error(
        f"Tuần {selected_week} không tồn tại trong năm {selected_year}."
    )
    st.stop()


time_range_str = (
    f"{first_day_of_week.strftime('%d/%m/%Y')}"
    f" - "
    f"{last_day_of_week.strftime('%d/%m/%Y')}"
)

st.subheader(
    f"Tuần {selected_week} ({time_range_str})"
)


# =========================================================
# SESSION STATE KEYS
# =========================================================

week_key = (
    f"df_simple_"
    f"{selected_year}_"
    f"{selected_week}"
)

ai_key = (
    f"ai_task_order_"
    f"{selected_year}_"
    f"{selected_week}"
)

ai_source_key = (
    f"{ai_key}_source"
)

sort_key = (
    f"sort_option_"
    f"{selected_year}_"
    f"{selected_week}"
)

editor_key = (
    f"editor_simple_"
    f"{selected_year}_"
    f"{selected_week}"
)


# =========================================================
# LOAD DATA
# =========================================================

if week_key not in st.session_state:

    st.session_state[week_key] = load_weekly_sheet(
        selected_year,
        selected_week,
    )


df = st.session_state[week_key]


if not isinstance(df, pd.DataFrame):
    df = pd.DataFrame(columns=COLUMNS)


# =========================================================
# NORMALIZE COLUMNS
# =========================================================

for column in COLUMNS:

    if column not in df.columns:

        if column == "Trạng thái":
            df[column] = False

        elif column == "Deadline":
            df[column] = pd.NaT

        else:
            df[column] = ""


df = df[COLUMNS].copy()


# =========================================================
# NORMALIZE DEADLINE
# =========================================================

df["Deadline"] = pd.to_datetime(
    df["Deadline"],
    errors="coerce",
    dayfirst=True,
)


# =========================================================
# SORT OPTION
# =========================================================

st.markdown("#### Sắp xếp công việc")


sort_option = st.selectbox(
    "Sắp xếp theo mức độ ưu tiên",
    [
        "Mặc định",
        "Cao → Thấp",
        "Thấp → Cao",
    ],
    key=sort_key,
)


priority_high_to_low = {
    "Cao": 1,
    "Trung bình": 2,
    "Thấp": 3,
}

priority_low_to_high = {
    "Thấp": 1,
    "Trung bình": 2,
    "Cao": 3,
}


display_df = df.copy()


if sort_option == "Cao → Thấp":

    display_df["_priority_order"] = (
        display_df["Mức độ ưu tiên"]
        .map(priority_high_to_low)
        .fillna(99)
    )

    display_df = (
        display_df
        .sort_values(
            "_priority_order",
            kind="stable",
        )
        .drop(
            columns=["_priority_order"]
        )
        .reset_index(drop=True)
    )


elif sort_option == "Thấp → Cao":

    display_df["_priority_order"] = (
        display_df["Mức độ ưu tiên"]
        .map(priority_low_to_high)
        .fillna(99)
    )

    display_df = (
        display_df
        .sort_values(
            "_priority_order",
            kind="stable",
        )
        .drop(
            columns=["_priority_order"]
        )
        .reset_index(drop=True)
    )


# =========================================================
# METRICS
# =========================================================

if not df.empty:

    valid_mask = (
        df["Tên công việc"]
        .astype(str)
        .str.strip()
        != ""
    )

    total_tasks = int(
        valid_mask.sum()
    )

else:

    valid_mask = pd.Series(dtype=bool)
    total_tasks = 0


if total_tasks > 0:

    completed_tasks = int(
        df.loc[
            valid_mask,
            "Trạng thái",
        ]
        .fillna(False)
        .astype(bool)
        .sum()
    )

else:

    completed_tasks = 0


pending_tasks = (
    total_tasks
    - completed_tasks
)


overall_percent = (
    completed_tasks
    / total_tasks
    * 100

    if total_tasks > 0

    else 0.0
)


metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Tổng công việc",
    total_tasks,
)

metric2.metric(
    "Đã hoàn thành",
    f"{completed_tasks} ({overall_percent:.1f}%)",
)

metric3.metric(
    "Chưa hoàn thành",
    pending_tasks,
)


st.progress(
    overall_percent / 100
    if total_tasks > 0
    else 0.0
)

st.divider()


# =========================================================
# TABLE CONFIG
# =========================================================

column_config = {

    "Tên công việc":
        st.column_config.TextColumn(
            "Công việc",
            required=True,
            width="large",
        ),

    "Mức độ ưu tiên":
        st.column_config.SelectboxColumn(
            "Mức độ ưu tiên",
            options=[
                "Cao",
                "Trung bình",
                "Thấp",
            ],
            default="Trung bình",
            width="medium",
        ),

    "Deadline":
        st.column_config.DatetimeColumn(
            "Deadline",
            format="DD/MM/YYYY HH:mm",
            step=900,
            width="medium",
        ),

    "Ghi chú":
        st.column_config.TextColumn(
            "Ghi chú",
            width="large",
        ),

    "Trạng thái":
        st.column_config.CheckboxColumn(
            "Trạng thái",
            default=False,
            width="small",
        ),
}


# =========================================================
# DATA EDITOR
# =========================================================

edited_df = st.data_editor(
    display_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config=column_config,
    key=editor_key,
)


# =========================================================
# AI TASK SORTING
# =========================================================

st.divider()

st.subheader(
    "AI hỗ trợ sắp xếp công việc"
)

st.caption(
    "AI phân tích trực tiếp các công việc đang có trong bảng, "
    "kể cả những thay đổi chưa lưu lên Google Sheets."
)


tasks_for_ai = edited_df.copy()


# Chỉ giữ các dòng có tên công việc
tasks_for_ai = tasks_for_ai[
    tasks_for_ai["Tên công việc"]
    .astype(str)
    .str.strip()
    != ""
].copy()


# Reset index để AI nhận ID ổn định
tasks_for_ai = tasks_for_ai.reset_index(
    drop=True
)


if st.button(
    "🤖 AI gợi ý thứ tự công việc",
    key=f"btn_ai_{selected_year}_{selected_week}",
):

    if tasks_for_ai.empty:

        st.warning(
            "Chưa có công việc để AI phân tích."
        )

    else:

        with st.spinner(
            "AI đang phân tích mức độ ưu tiên, deadline và ghi chú..."
        ):

            try:

                ai_result = suggest_task_order(
                    tasks_for_ai
                )


                if not ai_result:

                    st.warning(
                        "AI chưa trả về gợi ý nào."
                    )

                else:

                    st.session_state[
                        ai_key
                    ] = ai_result

                    st.session_state[
                        ai_source_key
                    ] = tasks_for_ai.copy()

                    st.rerun()


            except Exception as e:

                st.error(
                    "Không thể lấy gợi ý từ AI."
                )

                st.code(
                    f"{type(e).__name__}: {e}"
                )


# =========================================================
# AI PREVIEW
# =========================================================

if (
    ai_key in st.session_state
    and
    ai_source_key in st.session_state
):

    ai_result = st.session_state[
        ai_key
    ]

    ai_source_df = st.session_state[
        ai_source_key
    ].copy()


    st.markdown(
        "#### Thứ tự AI đề xuất"
    )


    preview_rows = []


    for position, item in enumerate(
        ai_result,
        start=1,
    ):

        task_id = item.get(
            "id"
        )


        if task_id not in ai_source_df.index:
            continue


        row = ai_source_df.loc[
            task_id
        ]


        deadline_value = row.get(
            "Deadline",
            pd.NaT,
        )


        deadline_display = ""


        if pd.notna(
            deadline_value
        ):

            deadline_value = pd.to_datetime(
                deadline_value,
                errors="coerce",
            )


            if pd.notna(
                deadline_value
            ):

                deadline_display = (
                    deadline_value.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                )


        note_value = row.get(
            "Ghi chú",
            "",
        )


        if pd.isna(note_value):
            note_value = ""


        preview_rows.append(
            {
                "Thứ tự": position,

                "Công việc":
                    row.get(
                        "Tên công việc",
                        "",
                    ),

                "Ưu tiên":
                    row.get(
                        "Mức độ ưu tiên",
                        "",
                    ),

                "Deadline":
                    deadline_display,

                "Ghi chú":
                    note_value,

                "Lý do AI":
                    item.get(
                        "reason",
                        "",
                    ),
            }
        )


    preview_df = pd.DataFrame(
        preview_rows
    )


    if not preview_df.empty:

        st.dataframe(
            preview_df,
            use_container_width=True,
            hide_index=True,
        )


    col_accept, col_cancel = st.columns(2)


    # =====================================================
    # ACCEPT AI ORDER
    # =====================================================

    with col_accept:

        if st.button(
            "✅ Chấp nhận thứ tự AI",
            type="primary",
            key=f"accept_ai_{selected_year}_{selected_week}",
        ):

            ordered_ids = []


            for item in ai_result:

                task_id = item.get(
                    "id"
                )


                if (
                    task_id
                    in ai_source_df.index
                    and
                    task_id
                    not in ordered_ids
                ):

                    ordered_ids.append(
                        task_id
                    )


            remaining_ids = [
                idx
                for idx
                in ai_source_df.index
                if idx not in ordered_ids
            ]


            final_order = (
                ordered_ids
                + remaining_ids
            )


            sorted_df = (
                ai_source_df.loc[
                    final_order
                ]
                .reset_index(
                    drop=True
                )
            )


            # Đưa dữ liệu AI đã sắp về bảng chính
            st.session_state[
                week_key
            ] = sorted_df


            # Xóa kết quả AI cũ
            del st.session_state[
                ai_key
            ]

            del st.session_state[
                ai_source_key
            ]


            # Sort thủ công quay về mặc định
            st.session_state[
                sort_key
            ] = "Mặc định"


            # Xóa state editor cũ
            # để bảng dựng lại theo thứ tự mới
            if (
                editor_key
                in st.session_state
            ):

                del st.session_state[
                    editor_key
                ]


            st.rerun()


    # =====================================================
    # CANCEL AI
    # =====================================================

    with col_cancel:

        if st.button(
            "❌ Bỏ gợi ý AI",
            key=f"cancel_ai_{selected_year}_{selected_week}",
        ):

            del st.session_state[
                ai_key
            ]

            del st.session_state[
                ai_source_key
            ]

            st.rerun()


# =========================================================
# SAVE BUTTON
# =========================================================

st.divider()


if st.button(
    "💾 Lưu & Đồng bộ Google Sheets",
    type="primary",
    key=f"save_{selected_year}_{selected_week}",
):

    clean_df = edited_df.copy()


    # Chỉ giữ dòng có tên công việc
    clean_df = clean_df[
        clean_df["Tên công việc"]
        .astype(str)
        .str.strip()
        != ""
    ].copy()


    # Đảm bảo đủ cột
    for column in COLUMNS:

        if column not in clean_df.columns:

            if column == "Trạng thái":
                clean_df[column] = False

            elif column == "Deadline":
                clean_df[column] = pd.NaT

            else:
                clean_df[column] = ""


    clean_df = clean_df[
        COLUMNS
    ].copy()


    # Chuẩn hóa deadline
    clean_df["Deadline"] = pd.to_datetime(
        clean_df["Deadline"],
        errors="coerce",
        dayfirst=True,
    )


    # Chuẩn hóa trạng thái
    clean_df["Trạng thái"] = (
        clean_df["Trạng thái"]
        .fillna(False)
        .astype(bool)
    )


    with st.spinner(
        "Đang đồng bộ với Google Sheets..."
    ):

        success = save_weekly_sheet(
            selected_year,
            selected_week,
            time_range_str,
            clean_df,
        )


    if success:

        st.session_state[
            week_key
        ] = clean_df.reset_index(
            drop=True
        )


        # Xóa preview AI cũ nếu còn
        if ai_key in st.session_state:

            del st.session_state[
                ai_key
            ]


        if ai_source_key in st.session_state:

            del st.session_state[
                ai_source_key
            ]


        st.success(
            f"Đã lưu tiến độ Tuần "
            f"{selected_week} "
            f"({time_range_str}) "
            f"vào Google Sheets thành công!"
        )


        st.rerun()


# =========================================================
# PENDING TASK REPORT
# =========================================================

st.divider()


if not edited_df.empty:

    report_df = edited_df[
        edited_df["Tên công việc"]
        .astype(str)
        .str.strip()
        != ""
    ].copy()

else:

    report_df = pd.DataFrame(
        columns=COLUMNS
    )


if not report_df.empty:

    report_df["Trạng thái"] = (
        report_df["Trạng thái"]
        .fillna(False)
        .astype(bool)
    )


    pending_df = report_df[
        ~report_df[
            "Trạng thái"
        ]
    ]


    st.subheader(
        "Báo cáo danh sách chưa đạt"
    )


    if not pending_df.empty:

        st.write(
            "Các công việc chưa hoàn thành trong tuần:"
        )


        for _, row in pending_df.iterrows():

            task_name = str(
                row.get(
                    "Tên công việc",
                    "",
                )
            ).strip()


            priority = str(
                row.get(
                    "Mức độ ưu tiên",
                    "",
                )
            ).strip()


            note = row.get(
                "Ghi chú",
                "",
            )


            if pd.isna(note):
                note = ""

            else:
                note = str(
                    note
                ).strip()


            deadline_value = row.get(
                "Deadline",
                pd.NaT,
            )


            deadline_str = ""


            if pd.notna(
                deadline_value
            ):

                deadline_value = pd.to_datetime(
                    deadline_value,
                    errors="coerce",
                )


                if pd.notna(
                    deadline_value
                ):

                    deadline_str = (
                        " | Deadline: "
                        + deadline_value.strftime(
                            "%d/%m/%Y %H:%M"
                        )
                    )


            note_str = ""


            if note:

                note_str = (
                    f" | Ghi chú: {note}"
                )


            st.write(
                f"- **{task_name}** "
                f"(Mức độ: "
                f"{priority}"
                f"{deadline_str}"
                f"{note_str})"
            )


    else:

        st.info(
            "Tất cả công việc trong tuần đã hoàn thành!"
        )


elif total_tasks == 0:

    st.info(
        "Chưa có công việc nào trong tuần này."
    )
