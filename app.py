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


for column in COLUMNS:
    if column not in df.columns:
        df[column] = False if column == "Trạng thái" else ""


df = df[COLUMNS].copy()


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

    total_tasks = int(valid_mask.sum())

else:
    total_tasks = 0


if total_tasks > 0:
    completed_tasks = int(
        df.loc[valid_mask, "Trạng thái"]
        .fillna(False)
        .astype(bool)
        .sum()
    )

else:
    completed_tasks = 0


pending_tasks = total_tasks - completed_tasks


overall_percent = (
    completed_tasks / total_tasks * 100
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
    "Tên công việc": st.column_config.TextColumn(
        "Công việc",
        required=True,
        width="large",
    ),

    "Mức độ ưu tiên": st.column_config.SelectboxColumn(
        "Mức độ ưu tiên",
        options=[
            "Cao",
            "Trung bình",
            "Thấp",
        ],
        default="Trung bình",
        width="medium",
    ),

    "Deadline": st.column_config.TextColumn(
        "Deadline (nếu có)",
        width="medium",
    ),

    "Trạng thái": st.column_config.CheckboxColumn(
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
    key=f"editor_simple_{selected_year}_{selected_week}",
)


# =========================================================
# SAVE BUTTON
# =========================================================

if st.button(
    "Lưu & Đồng bộ Google Sheets",
    type="primary",
):

    clean_df = edited_df.copy()

    clean_df = clean_df[
        clean_df["Tên công việc"]
        .astype(str)
        .str.strip()
        != ""
    ].copy()


    for column in COLUMNS:
        if column not in clean_df.columns:
            clean_df[column] = (
                False if column == "Trạng thái" else ""
            )


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

        st.session_state[week_key] = clean_df

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
        ~report_df["Trạng thái"]
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
                row.get("Tên công việc", "")
            ).strip()

            priority = str(
                row.get("Mức độ ưu tiên", "")
            ).strip()

            deadline = str(
                row.get("Deadline", "")
            ).strip()


            deadline_str = ""

            if (
                deadline
                and deadline.lower() != "nan"
            ):

                deadline_str = (
                    f" | Deadline: {deadline}"
                )


            st.write(
                f"- **{task_name}** "
                f"(Mức độ: "
                f"{priority}"
                f"{deadline_str})"
            )

    else:

        st.info(
            "Tất cả công việc trong tuần đã hoàn thành!"
        )
