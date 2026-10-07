import datetime

import pandas as pd
import streamlit as st

from sheets_db import (
    COLUMNS,
    load_weekly_sheet,
    save_weekly_sheet,
)

from task_scheduler import (
    suggest_task_order,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Weekly Task Planner",
    page_icon="📅",
    layout="wide",
)

st.title(
    "Quản Lý Công Việc Theo Tuần"
)


# =========================================================
# CURRENT WEEK
# =========================================================

today = datetime.date.today()

current_year, current_week, _ = (
    today.isocalendar()
)


# =========================================================
# WEEK SELECTOR
# =========================================================

col_year, col_week = st.columns(2)


with col_year:

    selected_year = st.number_input(
        "Năm",
        min_value=2024,
        max_value=2035,
        value=int(current_year),
        step=1,
    )


with col_week:

    selected_week = st.number_input(
        "Tuần thứ",
        min_value=1,
        max_value=53,
        value=int(current_week),
        step=1,
    )


selected_year = int(
    selected_year
)

selected_week = int(
    selected_week
)


# =========================================================
# WEEK RANGE
# =========================================================

try:

    first_day_of_week = (
        datetime.date.fromisocalendar(
            selected_year,
            selected_week,
            1,
        )
    )

    last_day_of_week = (
        datetime.date.fromisocalendar(
            selected_year,
            selected_week,
            7,
        )
    )

except ValueError:

    st.error(
        f"Tuần {selected_week} "
        f"không tồn tại trong "
        f"năm {selected_year}."
    )

    st.stop()


time_range_str = (
    f"{first_day_of_week.strftime('%d/%m/%Y')}"
    f" - "
    f"{last_day_of_week.strftime('%d/%m/%Y')}"
)


st.subheader(
    f"Tuần {selected_week} "
    f"({time_range_str})"
)


week_start_ts = pd.Timestamp(
    first_day_of_week
)

week_end_ts = (
    pd.Timestamp(
        last_day_of_week
    )
    + pd.Timedelta(days=1)
    - pd.Timedelta(seconds=1)
)


# =========================================================
# SESSION KEYS
# =========================================================

week_key = (
    f"weekly_data_"
    f"{selected_year}_"
    f"{selected_week}"
)


editor_key = (
    f"editor_"
    f"{selected_year}_"
    f"{selected_week}"
)


suggest_key = (
    f"suggest_"
    f"{selected_year}_"
    f"{selected_week}"
)


suggest_source_key = (
    f"{suggest_key}_source"
)


sort_key = (
    f"sort_"
    f"{selected_year}_"
    f"{selected_week}"
)


# =========================================================
# LOAD DATA
# =========================================================

if week_key not in st.session_state:

    st.session_state[
        week_key
    ] = load_weekly_sheet(
        selected_year,
        selected_week,
    )


df = st.session_state[
    week_key
].copy()


# =========================================================
# ENSURE DISPLAY COLUMNS
# =========================================================

required_columns = [
    "Task ID",
    "Năm gốc",
    "Tuần gốc",
    "Mốc thời gian",
    "Ngày hoàn thành",
    "Tên công việc",
    "Mức độ ưu tiên",
    "Deadline",
    "Ghi chú",
    "Trạng thái",
    "Nguồn",
]


for column in required_columns:

    if column not in df.columns:

        if column == "Trạng thái":

            df[column] = False

        elif column in [
            "Deadline",
            "Ngày hoàn thành",
        ]:

            df[column] = pd.NaT

        else:

            df[column] = ""


df["Deadline"] = pd.to_datetime(
    df["Deadline"],
    errors="coerce",
    dayfirst=True,
)


df["Ngày hoàn thành"] = pd.to_datetime(
    df["Ngày hoàn thành"],
    errors="coerce",
    dayfirst=True,
)


# =========================================================
# SORT
# =========================================================

st.markdown(
    "#### Sắp xếp công việc"
)


sort_option = st.selectbox(
    "Thứ tự hiển thị",
    [
        "Mặc định",
        "Cao → Thấp",
        "Thấp → Cao",
    ],
    key=sort_key,
)


display_df = df.copy()


priority_high = {
    "Cao": 0,
    "Trung bình": 1,
    "Thấp": 2,
}


priority_low = {
    "Thấp": 0,
    "Trung bình": 1,
    "Cao": 2,
}


if sort_option == "Cao → Thấp":

    display_df["_priority"] = (
        display_df[
            "Mức độ ưu tiên"
        ]
        .map(
            priority_high
        )
        .fillna(99)
    )

    display_df = (
        display_df
        .sort_values(
            "_priority",
            kind="stable",
        )
        .drop(
            columns=[
                "_priority"
            ]
        )
        .reset_index(
            drop=True
        )
    )


elif sort_option == "Thấp → Cao":

    display_df["_priority"] = (
        display_df[
            "Mức độ ưu tiên"
        ]
        .map(
            priority_low
        )
        .fillna(99)
    )

    display_df = (
        display_df
        .sort_values(
            "_priority",
            kind="stable",
        )
        .drop(
            columns=[
                "_priority"
            ]
        )
        .reset_index(
            drop=True
        )
    )


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
            "Hoàn thành",
            default=False,
            width="small",
        ),
}


# =========================================================
# EDITOR
# =========================================================

edited_df = st.data_editor(
    display_df,

    num_rows="dynamic",

    use_container_width=True,

    column_config=column_config,

    column_order=[
        "Tên công việc",
        "Mức độ ưu tiên",
        "Deadline",
        "Ghi chú",
        "Trạng thái",
    ],

    key=editor_key,
)


# =========================================================
# LIVE METRICS
# =========================================================

valid_df = edited_df[
    edited_df[
        "Tên công việc"
    ]
    .astype(str)
    .str.strip()
    != ""
].copy()


# ---------------------------------------------------------
# TASK SINH RA TUẦN NÀY
# ---------------------------------------------------------

origin_this_week = (
    pd.to_numeric(
        valid_df[
            "Năm gốc"
        ],
        errors="coerce",
    )
    == selected_year
) & (
    pd.to_numeric(
        valid_df[
            "Tuần gốc"
        ],
        errors="coerce",
    )
    == selected_week
)


# Các dòng mới chưa có tuần gốc
new_rows = (
    pd.to_numeric(
        valid_df[
            "Năm gốc"
        ],
        errors="coerce",
    ).isna()
)


origin_this_week = (
    origin_this_week
    |
    new_rows
)


this_week_df = valid_df[
    origin_this_week
].copy()


carryover_df = valid_df[
    ~origin_this_week
].copy()


total_this_week = len(
    this_week_df
)


# =========================================================
# ON-TIME COMPLETION
# =========================================================

completed_on_time = 0

late_from_this_week = 0


for _, row in this_week_df.iterrows():

    completion = pd.to_datetime(
        row.get(
            "Ngày hoàn thành"
        ),
        errors="coerce",
    )


    # Nếu vừa tick trong editor và chưa save,
    # coi như hoàn thành trong tuần hiện tại
    # nếu đang xem chính tuần hiện tại.
    if (
        bool(
            row.get(
                "Trạng thái",
                False,
            )
        )
        and
        pd.isna(completion)
        and
        selected_year == current_year
        and
        selected_week == current_week
    ):

        completion = pd.Timestamp.now()


    if pd.notna(
        completion
    ):

        if (
            week_start_ts
            <= completion
            <= week_end_ts
        ):

            completed_on_time += 1

        elif completion > week_end_ts:

            late_from_this_week += 1


completion_percent = (
    completed_on_time
    / total_this_week
    * 100

    if total_this_week > 0

    else 0.0
)


pending_this_week = (
    total_this_week
    - completed_on_time
    - late_from_this_week
)


# =========================================================
# CARRYOVER METRICS
# =========================================================

carryover_total = len(
    carryover_df
)


carryover_done = int(
    carryover_df[
        "Trạng thái"
    ]
    .fillna(False)
    .astype(bool)
    .sum()
)


# =========================================================
# METRIC CARDS
# =========================================================

st.divider()


m1, m2, m3, m4, m5 = (
    st.columns(5)
)


m1.metric(
    "Công việc tuần",
    total_this_week,
)


m2.metric(
    "Hoàn thành đúng tuần",
    (
        f"{completed_on_time} "
        f"({completion_percent:.1f}%)"
    ),
)


m3.metric(
    "Chưa hoàn thành",
    pending_this_week,
)


m4.metric(
    "Tồn từ tuần trước",
    carryover_total,
)


m5.metric(
    "Đã xử lý tồn",
    carryover_done,
)


st.progress(
    completion_percent / 100
    if total_this_week > 0
    else 0.0
)


if late_from_this_week > 0:

    st.warning(
        f"{late_from_this_week} công việc "
        f"của tuần này được hoàn thành trễ."
    )


# =========================================================
# LOCAL SCHEDULER
# =========================================================

st.divider()

st.subheader(
    "Gợi ý sắp xếp công việc"
)


st.caption(
    "Gợi ý chạy trực tiếp bằng Python, "
    "không dùng API và không mất phí."
)


tasks_for_sort = (
    valid_df.reset_index(
        drop=True
    )
)


if st.button(
    "✨ Gợi ý thứ tự công việc",
    key=(
        f"btn_{suggest_key}"
    ),
):

    if tasks_for_sort.empty:

        st.warning(
            "Chưa có công việc để sắp xếp."
        )

    else:

        result = (
            suggest_task_order(
                tasks_for_sort
            )
        )

        st.session_state[
            suggest_key
        ] = result

        st.session_state[
            suggest_source_key
        ] = tasks_for_sort.copy()

        st.rerun()


# =========================================================
# PREVIEW SUGGESTION
# =========================================================

if (
    suggest_key
    in st.session_state
    and
    suggest_source_key
    in st.session_state
):

    suggestions = (
        st.session_state[
            suggest_key
        ]
    )

    source_df = (
        st.session_state[
            suggest_source_key
        ].copy()
    )

    preview = []


    for position, item in enumerate(
        suggestions,
        start=1,
    ):

        task_id = item[
            "id"
        ]


        if task_id not in source_df.index:
            continue


        row = source_df.loc[
            task_id
        ]


        deadline = row.get(
            "Deadline",
            pd.NaT,
        )


        if pd.notna(
            deadline
        ):

            deadline_text = (
                pd.to_datetime(
                    deadline
                ).strftime(
                    "%d/%m/%Y %H:%M"
                )
            )

        else:

            deadline_text = ""


        preview.append(
            {
                "Thứ tự":
                    position,

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
                    deadline_text,

                "Lý do":
                    item.get(
                        "reason",
                        "",
                    ),
            }
        )


    st.markdown(
        "#### Thứ tự được đề xuất"
    )


    st.dataframe(
        pd.DataFrame(
            preview
        ),
        use_container_width=True,
        hide_index=True,
    )


    accept_col, cancel_col = (
        st.columns(2)
    )


    with accept_col:

        if st.button(
            "✅ Chấp nhận thứ tự",
            type="primary",
        ):

            ordered_ids = [
                item["id"]
                for item
                in suggestions
                if item["id"]
                in source_df.index
            ]


            remaining_ids = [
                idx
                for idx
                in source_df.index
                if idx
                not in ordered_ids
            ]


            ordered_df = (
                source_df.loc[
                    ordered_ids
                    + remaining_ids
                ]
                .reset_index(
                    drop=True
                )
            )


            st.session_state[
                week_key
            ] = ordered_df


            del st.session_state[
                suggest_key
            ]

            del st.session_state[
                suggest_source_key
            ]


            st.session_state[
                sort_key
            ] = "Mặc định"


            if (
                editor_key
                in st.session_state
            ):

                del st.session_state[
                    editor_key
                ]


            st.rerun()


    with cancel_col:

        if st.button(
            "❌ Bỏ gợi ý"
        ):

            del st.session_state[
                suggest_key
            ]

            del st.session_state[
                suggest_source_key
            ]

            st.rerun()


# =========================================================
# SAVE
# =========================================================

st.divider()


if st.button(
    "💾 Lưu & Đồng bộ Google Sheets",
    type="primary",
):

    clean_df = edited_df[
        edited_df[
            "Tên công việc"
        ]
        .astype(str)
        .str.strip()
        != ""
    ].copy()


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

        # Reload từ database để nhận:
        # - Task ID mới
        # - Ngày hoàn thành mới
        # - trạng thái carryover mới
        st.session_state[
            week_key
        ] = load_weekly_sheet(
            selected_year,
            selected_week,
        )


        if (
            editor_key
            in st.session_state
        ):

            del st.session_state[
                editor_key
            ]


        st.success(
            "Đã lưu và đồng bộ "
            "Google Sheets thành công!"
        )


        st.rerun()


# =========================================================
# PENDING REPORT
# =========================================================

st.divider()

st.subheader(
    "Công việc chưa hoàn thành"
)


pending_df = valid_df[
    ~valid_df[
        "Trạng thái"
    ]
    .fillna(False)
    .astype(bool)
].copy()


if pending_df.empty:

    st.info(
        "Không còn công việc "
        "chưa hoàn thành."
    )

else:

    for _, row in pending_df.iterrows():

        task = str(
            row.get(
                "Tên công việc",
                "",
            )
        )


        priority = str(
            row.get(
                "Mức độ ưu tiên",
                "",
            )
        )


        deadline = row.get(
            "Deadline",
            pd.NaT,
        )


        deadline_text = ""


        if pd.notna(
            deadline
        ):

            deadline_text = (
                " | Deadline: "
                + pd.to_datetime(
                    deadline
                ).strftime(
                    "%d/%m/%Y %H:%M"
                )
            )


        st.write(
            f"- **{task}** "
            f"| {priority}"
            f"{deadline_text}"
        )
