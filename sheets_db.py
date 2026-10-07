import datetime
import uuid

import gspread
import pandas as pd
import streamlit as st


# =========================================================
# COLUMNS HIỂN THỊ
# =========================================================

COLUMNS = [
    "Tên công việc",
    "Mức độ ưu tiên",
    "Deadline",
    "Ghi chú",
    "Trạng thái",
]


# =========================================================
# COLUMNS HỆ THỐNG
# =========================================================

SYSTEM_COLUMNS = [
    "Task ID",
    "Năm gốc",
    "Tuần gốc",
    "Mốc thời gian",
    "Ngày hoàn thành",
]


SHEET_HEADERS = [
    "Task ID",
    "Năm gốc",
    "Tuần gốc",
    "Mốc thời gian",
    "Tên công việc",
    "Mức độ ưu tiên",
    "Deadline",
    "Ghi chú",
    "Trạng thái",
    "Ngày hoàn thành",
]


WORKSHEET_NAME = "Simple_Weekly_Tasks"


# =========================================================
# GOOGLE CLIENT
# =========================================================

def get_google_client():

    service_account_info = dict(
        st.secrets["gcp_service_account"]
    )

    return gspread.service_account_from_dict(
        service_account_info
    )


def get_spreadsheet():

    spreadsheet_id = str(
        st.secrets["spreadsheet_id"]
    ).strip()

    gc = get_google_client()

    gc.http_client.fetch_sheet_metadata(
        spreadsheet_id
    )

    return gc.open_by_key(
        spreadsheet_id
    )


# =========================================================
# WORKSHEET
# =========================================================

def get_or_create_worksheet(spreadsheet):

    try:
        return spreadsheet.worksheet(
            WORKSHEET_NAME
        )

    except gspread.exceptions.WorksheetNotFound:

        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=1000,
            cols=15,
        )

        worksheet.append_row(
            SHEET_HEADERS
        )

        return worksheet


# =========================================================
# HELPERS
# =========================================================

def parse_status(value):

    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()

    return value in [
        "true",
        "1",
        "x",
        "yes",
        "done",
        "hoàn thành",
        "đã hoàn thành",
    ]


def parse_datetime(value):

    if value is None:
        return pd.NaT

    text = str(value).strip()

    if (
        text == ""
        or text.lower()
        in ["nan", "nat", "none"]
    ):
        return pd.NaT

    return pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=True,
    )


def week_start(year, week):

    return pd.Timestamp(
        datetime.date.fromisocalendar(
            int(year),
            int(week),
            1,
        )
    )


def week_end(year, week):

    # 23:59:59 ngày Chủ nhật
    return (
        pd.Timestamp(
            datetime.date.fromisocalendar(
                int(year),
                int(week),
                7,
            )
        )
        + pd.Timedelta(days=1)
        - pd.Timedelta(seconds=1)
    )


def make_task_id():

    return uuid.uuid4().hex


# =========================================================
# MIGRATION / NORMALIZATION
# =========================================================

def normalize_database(df):

    """
    Chuyển cả dữ liệu sheet cũ và mới
    về cùng một cấu trúc.
    """

    if df is None or df.empty:

        return pd.DataFrame(
            columns=SHEET_HEADERS
        )


    df = df.copy()


    # -----------------------------------------------------
    # MIGRATE VERSION CŨ:
    # Năm -> Năm gốc
    # Tuần -> Tuần gốc
    # -----------------------------------------------------

    if (
        "Năm gốc" not in df.columns
        and "Năm" in df.columns
    ):

        df["Năm gốc"] = df["Năm"]


    if (
        "Tuần gốc" not in df.columns
        and "Tuần" in df.columns
    ):

        df["Tuần gốc"] = df["Tuần"]


    # -----------------------------------------------------
    # OLD STATUS
    # -----------------------------------------------------

    if (
        "Trạng thái" not in df.columns
        and "Đã xong" in df.columns
    ):

        df["Trạng thái"] = df[
            "Đã xong"
        ]


    # -----------------------------------------------------
    # ENSURE ALL COLUMNS
    # -----------------------------------------------------

    for column in SHEET_HEADERS:

        if column not in df.columns:

            if column == "Trạng thái":
                df[column] = False

            else:
                df[column] = ""


    # -----------------------------------------------------
    # TASK ID
    # -----------------------------------------------------

    for index in df.index:

        task_id = str(
            df.at[index, "Task ID"]
        ).strip()

        if (
            not task_id
            or task_id.lower()
            in ["nan", "none"]
        ):

            df.at[
                index,
                "Task ID"
            ] = make_task_id()


    # -----------------------------------------------------
    # TYPES
    # -----------------------------------------------------

    df["Năm gốc"] = pd.to_numeric(
        df["Năm gốc"],
        errors="coerce",
    )

    df["Tuần gốc"] = pd.to_numeric(
        df["Tuần gốc"],
        errors="coerce",
    )

    df["Deadline"] = df[
        "Deadline"
    ].apply(
        parse_datetime
    )

    df["Ngày hoàn thành"] = df[
        "Ngày hoàn thành"
    ].apply(
        parse_datetime
    )

    df["Trạng thái"] = df[
        "Trạng thái"
    ].apply(
        parse_status
    )


    return df[
        SHEET_HEADERS
    ].copy()


# =========================================================
# READ DATABASE
# =========================================================

def read_database():

    spreadsheet = get_spreadsheet()

    worksheet = get_or_create_worksheet(
        spreadsheet
    )

    data = worksheet.get_all_records()

    if not data:

        return (
            pd.DataFrame(
                columns=SHEET_HEADERS
            ),
            worksheet,
        )

    df = pd.DataFrame(data)

    df = normalize_database(df)

    return df, worksheet


# =========================================================
# LOAD WEEK VIEW
# =========================================================

def load_weekly_sheet(
    year: int,
    week: int,
):

    """
    Trả về:
    - task sinh ra trong tuần đang xem
    - task tồn từ các tuần trước mà tại đầu tuần
      đang xem vẫn chưa hoàn thành
    """

    try:

        df_all, _ = read_database()


        if df_all.empty:

            empty_columns = (
                SYSTEM_COLUMNS
                + COLUMNS
                + ["Nguồn"]
            )

            return pd.DataFrame(
                columns=empty_columns
            )


        selected_start = week_start(
            year,
            week,
        )

        selected_end = week_end(
            year,
            week,
        )


        # =================================================
        # TASK GỐC CỦA TUẦN ĐANG XEM
        # =================================================

        current_week_mask = (
            (df_all["Năm gốc"] == year)
            &
            (df_all["Tuần gốc"] == week)
        )


        # =================================================
        # TASK CŨ
        # =================================================

        origin_dates = []


        for _, row in df_all.iterrows():

            try:

                origin_dates.append(
                    week_start(
                        int(row["Năm gốc"]),
                        int(row["Tuần gốc"]),
                    )
                )

            except Exception:

                origin_dates.append(
                    pd.NaT
                )


        df_all["_origin_start"] = (
            origin_dates
        )


        old_task = (
            df_all["_origin_start"]
            < selected_start
        )


        completion = (
            df_all["Ngày hoàn thành"]
        )


        # Task được xem là tồn trong tuần này nếu:
        # - chưa bao giờ hoàn thành
        # hoặc
        # - hoàn thành từ đầu tuần này trở đi
        carryover_alive = (
            completion.isna()
            |
            (
                completion
                >= selected_start
            )
        )


        carryover_mask = (
            old_task
            &
            carryover_alive
        )


        view_df = df_all[
            current_week_mask
            |
            carryover_mask
        ].copy()


        if view_df.empty:

            empty_columns = (
                SYSTEM_COLUMNS
                + COLUMNS
                + ["Nguồn"]
            )

            return pd.DataFrame(
                columns=empty_columns
            )


        # =================================================
        # TRẠNG THÁI THEO THỜI ĐIỂM TUẦN ĐANG XEM
        # =================================================

        # Nếu task hoàn thành sau tuần đang xem,
        # khi xem lại tuần cũ nó phải hiện là chưa hoàn thành.
        view_df["Trạng thái"] = (
            view_df["Ngày hoàn thành"]
            .notna()
            &
            (
                view_df["Ngày hoàn thành"]
                <= selected_end
            )
        )


        # =================================================
        # NGUỒN
        # =================================================

        def source_label(row):

            if (
                int(row["Năm gốc"]) == year
                and
                int(row["Tuần gốc"]) == week
            ):

                return "Tuần này"


            label = (
                f"Tồn từ tuần "
                f"{int(row['Tuần gốc'])}"
                f"/{int(row['Năm gốc'])}"
            )


            if (
                pd.notna(
                    row["Ngày hoàn thành"]
                )
                and
                selected_start
                <= row["Ngày hoàn thành"]
                <= selected_end
            ):

                label += " • hoàn thành trễ"


            return label


        view_df["Nguồn"] = (
            view_df.apply(
                source_label,
                axis=1,
            )
        )


        view_df = view_df.drop(
            columns=["_origin_start"],
            errors="ignore",
        )


        output_columns = (
            SYSTEM_COLUMNS
            + COLUMNS
            + ["Nguồn"]
        )


        return view_df[
            output_columns
        ].reset_index(
            drop=True
        )


    except Exception as e:

        st.error(
            f"Lỗi khi tải Google Sheets: "
            f"{type(e).__name__}"
        )

        st.code(
            repr(e)
        )

        return pd.DataFrame(
            columns=(
                SYSTEM_COLUMNS
                + COLUMNS
                + ["Nguồn"]
            )
        )


# =========================================================
# SAVE DATABASE
# =========================================================

def save_weekly_sheet(
    year: int,
    week: int,
    time_range_str: str,
    df_current: pd.DataFrame,
):

    """
    Đồng bộ view tuần hiện tại vào database chính.

    - Task mới -> tạo Task ID + tuần gốc hiện tại
    - Tick hoàn thành -> ghi Ngày hoàn thành
    - Task tồn -> giữ tuần gốc cũ
    - Bỏ tick task vừa hoàn thành -> xóa ngày hoàn thành
    - Xóa task thuộc chính tuần này -> xóa khỏi database
    - Không xóa task tồn chỉ vì nó biến mất khỏi view
    """

    try:

        df_all, worksheet = read_database()

        df_edit = df_current.copy()


        # =================================================
        # ENSURE COLUMNS
        # =================================================

        required_view_columns = (
            SYSTEM_COLUMNS
            + COLUMNS
            + ["Nguồn"]
        )


        for column in required_view_columns:

            if column not in df_edit.columns:

                if column == "Trạng thái":
                    df_edit[column] = False

                elif column == "Deadline":
                    df_edit[column] = pd.NaT

                else:
                    df_edit[column] = ""


        # Chỉ giữ dòng có công việc
        df_edit = df_edit[
            df_edit["Tên công việc"]
            .astype(str)
            .str.strip()
            != ""
        ].copy()


        now = pd.Timestamp.now()


        # =================================================
        # PROCESS ROWS
        # =================================================

        saved_rows = []

        visible_task_ids = set()


        for _, row in df_edit.iterrows():

            task_id = str(
                row.get(
                    "Task ID",
                    "",
                )
            ).strip()


            is_new = (
                not task_id
                or task_id.lower()
                in ["nan", "none"]
            )


            if is_new:

                task_id = make_task_id()

                origin_year = year
                origin_week = week

                original_completion = pd.NaT

            else:

                origin_year = row.get(
                    "Năm gốc",
                    year,
                )

                origin_week = row.get(
                    "Tuần gốc",
                    week,
                )

                original_completion = parse_datetime(
                    row.get(
                        "Ngày hoàn thành"
                    )
                )


            # -------------------------------------------------
            # FALLBACK ORIGIN
            # -------------------------------------------------

            try:
                origin_year = int(
                    origin_year
                )

            except Exception:
                origin_year = year


            try:
                origin_week = int(
                    origin_week
                )

            except Exception:
                origin_week = week


            # -------------------------------------------------
            # STATUS / COMPLETION DATE
            # -------------------------------------------------

            current_status = bool(
                row.get(
                    "Trạng thái",
                    False,
                )
            )


            selected_end = week_end(
                year,
                week,
            )


            selected_start = week_start(
                year,
                week,
            )


            completion_date = (
                original_completion
            )


            if current_status:

                # Nếu chưa từng có ngày hoàn thành,
                # ghi nhận thời điểm hiện tại.
                if pd.isna(
                    completion_date
                ):

                    completion_date = now


            else:

                # Nếu completion ở sau tuần đang xem,
                # đó là dữ liệu lịch sử tương lai:
                # không xóa.
                if (
                    pd.notna(
                        completion_date
                    )
                    and
                    completion_date
                    > selected_end
                ):

                    pass

                else:

                    # Cho phép bỏ tick ở tuần hiện tại/
                    # tuần chứa completion.
                    completion_date = pd.NaT


            saved_rows.append(
                {
                    "Task ID": task_id,

                    "Năm gốc":
                        origin_year,

                    "Tuần gốc":
                        origin_week,

                    "Mốc thời gian":
                        row.get(
                            "Mốc thời gian",
                            time_range_str,
                        )
                        or time_range_str,

                    "Tên công việc":
                        str(
                            row.get(
                                "Tên công việc",
                                "",
                            )
                        ),

                    "Mức độ ưu tiên":
                        str(
                            row.get(
                                "Mức độ ưu tiên",
                                "Trung bình",
                            )
                        ),

                    "Deadline":
                        parse_datetime(
                            row.get(
                                "Deadline"
                            )
                        ),

                    "Ghi chú":
                        str(
                            row.get(
                                "Ghi chú",
                                "",
                            )
                        ),

                    "Trạng thái":
                        pd.notna(
                            completion_date
                        ),

                    "Ngày hoàn thành":
                        completion_date,
                }
            )


            visible_task_ids.add(
                task_id
            )


        df_saved = pd.DataFrame(
            saved_rows,
            columns=SHEET_HEADERS,
        )


        # =================================================
        # DELETE TASKS REMOVED FROM CURRENT WEEK
        # =================================================

        if not df_all.empty:

            current_week_existing = df_all[
                (df_all["Năm gốc"] == year)
                &
                (df_all["Tuần gốc"] == week)
            ]


            deleted_ids = set(
                current_week_existing[
                    "Task ID"
                ].astype(str)
            ) - visible_task_ids


            if deleted_ids:

                df_all = df_all[
                    ~df_all[
                        "Task ID"
                    ].astype(str).isin(
                        deleted_ids
                    )
                ].copy()


        # =================================================
        # UPSERT
        # =================================================

        if not df_saved.empty:

            saved_ids = set(
                df_saved[
                    "Task ID"
                ].astype(str)
            )


            if not df_all.empty:

                df_all = df_all[
                    ~df_all[
                        "Task ID"
                    ].astype(str).isin(
                        saved_ids
                    )
                ].copy()


            df_all = pd.concat(
                [
                    df_all,
                    df_saved,
                ],
                ignore_index=True,
            )


        df_all = normalize_database(
            df_all
        )


        # =================================================
        # SERIALIZE FOR GOOGLE SHEETS
        # =================================================

        output_df = df_all.copy()


        output_df[
            "Deadline"
        ] = output_df[
            "Deadline"
        ].apply(
            lambda x:
                x.strftime(
                    "%d/%m/%Y %H:%M"
                )
                if pd.notna(x)
                else ""
        )


        output_df[
            "Ngày hoàn thành"
        ] = output_df[
            "Ngày hoàn thành"
        ].apply(
            lambda x:
                x.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if pd.notna(x)
                else ""
        )


        output_df = output_df.fillna(
            ""
        )


        rows = []


        for row in output_df[
            SHEET_HEADERS
        ].itertuples(
            index=False,
            name=None,
        ):

            clean_row = []

            for value in row:

                if hasattr(
                    value,
                    "item",
                ):

                    try:
                        value = value.item()
                    except Exception:
                        pass

                clean_row.append(
                    value
                )

            rows.append(
                clean_row
            )


        worksheet.clear()


        worksheet.update(
            range_name="A1",
            values=[
                SHEET_HEADERS
            ] + rows,
        )


        return True


    except Exception as e:

        st.error(
            f"Lỗi khi lưu Google Sheets: "
            f"{type(e).__name__}"
        )

        st.code(
            repr(e)
        )

        return False
