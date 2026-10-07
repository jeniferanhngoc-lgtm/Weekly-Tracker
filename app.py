import datetime

import pandas as pd
import streamlit as st

from sheets_db import (
    COLUMNS,
    load_weekly_sheet,
    save_weekly_sheet,
)


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
# CURRENT WEEK
# =========================================================

today = datetime.date.today()
current_year, current_week, _ = today.isocalendar()


# =========================================================
# SELECT YEAR / WEEK
# =========================================================

col1, col2 = st.columns(2)

with col1:
    selected_year = st.number_input(
        "Năm",
        min_value=2024,
        max_value=2035,
        value=int(current_year),
        step=1,
    )

with col2:
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
# DATE RANGE
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
# SESSION STATE
# =========================================================

week_key = f"df_simple_{selected_year}_{selected_week}"


if week_key not in st.session_state:
    st.session_state[week_key] = load_weekly_sheet(
        selected_year,
        selected_week,
    )


df = st.session_state[week_key]


if not isinstance(df, pd.DataFrame):
    df = pd.DataFrame(columns=COLUMNS)


# Đảm bảo đủ cột
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
# CHUẨN HÓA DEADLINE
# =========================================================

df["Deadline"] = pd.to_datetime(
    df["Deadline"],
    errors="coerce",
    dayfirst=True,
)


# =========================================================
# SORT PRIORITY
# =========================================================

st.markdown("#### Sắp xếp công việc")

sort_option = st.selectbox(
    "Sắp xếp theo mức độ ưu tiên",
    [
        "Mặc định",
        "Cao → Thấp",
        "Thấp → Cao",
    ],
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


if sort_option == "Cao → Thấp":

    df["_priority_order"] = (
        df["Mức độ ưu tiên"]
        .map(priority_high_to_low)
        .fillna(99)
    )

    df = (
        df.sort_values(
            "_priority_order",
            kind="stable",
        )
        .drop(columns=["_priority_order"])
        .reset_index(drop=True)
    )


elif sort_option == "Thấp → Cao":

    df["_priority_order"] = (
        df["Mức độ ưu tiên"]
        .map(priority_low_to_high)
        .fillna(99)
    )

    df = (
        df.sort_values(
            "_priority_order",
            kind="stable",
        )
        .drop(columns=["_priority_order"])
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

    valid_mask = pd.Series(
        dtype=bool
    )

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
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config=column_config,
    key=f"editor_simple_{selected_year}_{selected_week}_{sort_option}",
)


# =========================================================
# SAVE BUTTON
# =========================================================

if st.button(
    "Lưu & Đồng bộ Google Sheets",
    type="primary",
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


    clean_df = clean_df[COLUMNS]


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
        ] = clean_df

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

    report_df[
        "Trạng thái"
    ] = (
        report_df[
            "Trạng thái"
        ]
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


            note = str(
                row.get(
                    "Ghi chú",
                    "",
                )
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
                    deadline_value
                )

                deadline_str = (
                    " | Deadline: "
                    + deadline_value.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                )


            note_str = ""

            if (
                note
                and note.lower()
                != "nan"
            ):

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
