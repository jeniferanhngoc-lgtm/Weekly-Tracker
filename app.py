import datetime

import pandas as pd
import streamlit as st

from sheets_db import (
    COLUMNS,
    load_weekly_sheet,
    save_weekly_sheet,
)


# =========================================================
# CẤU HÌNH TRANG
# =========================================================

st.set_page_config(
    page_title="Weekly Task Planner",
    page_icon="📅",
    layout="wide",
)

st.title("Quản Lý Công Việc Theo Tuần")


# =========================================================
# LẤY TUẦN HIỆN TẠI
# =========================================================

today = datetime.date.today()
current_year, current_week, _ = today.isocalendar()


# =========================================================
# CHỌN NĂM / TUẦN
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
# XÁC ĐỊNH KHOẢNG THỜI GIAN CỦA TUẦN
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
# SESSION STATE CHO TỪNG TUẦN
# =========================================================

week_key = f"df_simple_{selected_year}_{selected_week}"


if week_key not in st.session_state:

    df_loaded = load_weekly_sheet(
        selected_year,
        selected_week,
    )

    st.session_state[week_key] = df_loaded


df = st.session_state[week_key]


# =========================================================
# ĐẢM BẢO DATAFRAME CÓ ĐÚNG CỘT
# =========================================================

if df is None or not isinstance(df, pd.DataFrame):
    df = pd.DataFrame(columns=COLUMNS)

for column in COLUMNS:
    if column not in df.columns:
        if column == "Trạng thái":
            df[column] = False
        else:
            df[column] = ""

df = df[COLUMNS].copy()


# =========================================================
# THỐNG KÊ
# =========================================================

if not df.empty:

    valid_tasks = (
        df["Tên công việc"]
        .astype(str)
        .str.strip()
        != ""
    )

    total_tasks = int(valid_tasks.sum())

else:
    total_tasks = 0


if (
    total_tasks > 0
    and "Trạng thái" in df.columns
):

    completed_tasks = int(
        df.loc[
            df["Tên công việc"]
            .astype(str)
            .str.strip()
            != "",
            "Trạng thái",
        ]
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


col1, col2, col3 = st.columns(3)

col1.metric(
    "Tổng công việc",
    total_tasks,
)

col2.metric(
    "Đã hoàn thành",
    f"{completed_tasks} ({overall_percent:.1f}%)",
)

col3.metric(
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
# CẤU HÌNH BẢNG
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
        st.column_config.TextColumn(
            "Deadline (nếu có)",
            width="medium",
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
    key=f"editor_simple_{selected_year}_{selected_week}",
)


# =========================================================
# NÚT LƯU
# =========================================================

if st.button(
    "Lưu & Đồng bộ Google Sheets",
    type="primary",
):

    clean_df = edited_df.copy()

    # Chỉ giữ những dòng có tên công việc
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

            else:
                clean_df[column] = ""

    clean_df = clean_df[COLUMNS]

    # Chuyển trạng thái về boolean
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

    # Chỉ báo thành công nếu Google thực sự lưu được
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
# BÁO CÁO CÔNG VIỆC CHƯA HOÀN THÀNH
# =========================================================

st.divider()

if not edited_df.empty:

    clean_report_df = edited_df[
        edited_df["Tên công việc"]
        .astype(str)
        .str.strip()
        != ""
    ].copy()

else:
    clean_report_df = pd.DataFrame(
        columns=COLUMNS
    )


if not clean_report_df.empty:

    clean_report_df["Trạng thái"] = (
        clean_report_df["Trạng thái"]
        .fillna(False)
        .astype(bool)
    )

    pending_df = clean_report_df[
        ~clean_report_df["Trạng thái"]
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

            deadline = str(
                row.get(
                    "Deadline",
                    "",
                )
            ).strip()


            deadline_str = ""

            if deadline and deadline.lower() != "nan":

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
            "Tất cả công việc trong tuần "
            "đã hoàn thành!"
        )
