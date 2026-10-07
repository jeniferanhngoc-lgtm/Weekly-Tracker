import gspread
import pandas as pd
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

COLUMNS = [
    "Tên công việc",
    "Mức độ ưu tiên",
    "Deadline",
    "Trạng thái",
]


SHEET_HEADERS = [
    "Năm",
    "Tuần",
    "Mốc thời gian",
] + COLUMNS


WORKSHEET_NAME = "Simple_Weekly_Tasks"


# =========================================================
# GOOGLE SHEETS CONNECTION
# =========================================================

def get_google_client():
    """
    Tạo Google Sheets client từ Streamlit Secrets.
    """

    service_account_info = dict(
        st.secrets["gcp_service_account"]
    )

    return gspread.service_account_from_dict(
        service_account_info
    )


def get_spreadsheet():
    """
    Kết nối Spreadsheet.

    Kiểm tra metadata trực tiếp trước để giữ nguyên
    lỗi Google API thay vì để open_by_key() đổi thành
    PermissionError không có thông tin.
    """

    spreadsheet_id = str(
        st.secrets["spreadsheet_id"]
    ).strip()

    service_account_info = dict(
        st.secrets["gcp_service_account"]
    )

    gc = get_google_client()


    try:

        # Test Google Sheets API + permission
        gc.http_client.fetch_sheet_metadata(
            spreadsheet_id
        )

        return gc.open_by_key(
            spreadsheet_id
        )


    except gspread.exceptions.APIError as e:

        st.error(
            "Google Sheets API từ chối kết nối."
        )

        st.code(
            f"""Service account:
{service_account_info.get("client_email")}

Project ID:
{service_account_info.get("project_id")}

Spreadsheet ID:
{spreadsheet_id}

Lỗi Google API:
{repr(e)}
"""
        )

        raise


# =========================================================
# WORKSHEET
# =========================================================

def get_or_create_worksheet(
    spreadsheet,
):
    """
    Lấy worksheet Simple_Weekly_Tasks.
    Nếu chưa tồn tại thì tạo mới.
    """

    try:

        return spreadsheet.worksheet(
            WORKSHEET_NAME
        )

    except gspread.exceptions.WorksheetNotFound:

        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=500,
            cols=10,
        )

        worksheet.append_row(
            SHEET_HEADERS
        )

        return worksheet


# =========================================================
# STATUS NORMALIZATION
# =========================================================

def parse_status(value):
    """
    Chuyển trạng thái từ Google Sheets về boolean.
    """

    if isinstance(value, bool):
        return value


    normalized = (
        str(value)
        .strip()
        .lower()
    )


    return normalized in [
        "true",
        "1",
        "x",
        "yes",
        "done",
        "hoàn thành",
        "đã hoàn thành",
    ]


# =========================================================
# DATAFRAME NORMALIZATION
# =========================================================

def normalize_dataframe(df):
    """
    Chuẩn hóa DataFrame theo cấu trúc ứng dụng.
    """

    if df is None:

        return pd.DataFrame(
            columns=COLUMNS
        )


    df = df.copy()


    if (
        "Trạng thái" not in df.columns
        and
        "Đã xong" in df.columns
    ):

        df["Trạng thái"] = (
            df["Đã xong"]
            .apply(parse_status)
        )


    for column in COLUMNS:

        if column not in df.columns:

            df[column] = (
                False
                if column == "Trạng thái"
                else ""
            )


    df["Trạng thái"] = (
        df["Trạng thái"]
        .apply(parse_status)
    )


    return df[COLUMNS]


# =========================================================
# LOAD WEEK
# =========================================================

def load_weekly_sheet(
    year: int,
    week: int,
):
    """
    Tải dữ liệu theo năm và tuần.
    """

    try:

        spreadsheet = get_spreadsheet()

        worksheet = get_or_create_worksheet(
            spreadsheet
        )


        data = worksheet.get_all_records()


        if not data:

            return pd.DataFrame(
                columns=COLUMNS
            )


        df_all = pd.DataFrame(
            data
        )


        if "Năm" not in df_all.columns:

            st.error(
                'Google Sheet thiếu cột "Năm".'
            )

            return pd.DataFrame(
                columns=COLUMNS
            )


        if "Tuần" not in df_all.columns:

            st.error(
                'Google Sheet thiếu cột "Tuần".'
            )

            return pd.DataFrame(
                columns=COLUMNS
            )


        df_all["Năm"] = pd.to_numeric(
            df_all["Năm"],
            errors="coerce",
        )


        df_all["Tuần"] = pd.to_numeric(
            df_all["Tuần"],
            errors="coerce",
        )


        df_filtered = df_all[
            (
                df_all["Năm"] == year
            )
            &
            (
                df_all["Tuần"] == week
            )
        ].copy()


        if df_filtered.empty:

            return pd.DataFrame(
                columns=COLUMNS
            )


        return normalize_dataframe(
            df_filtered
        )


    except gspread.exceptions.APIError:

        return pd.DataFrame(
            columns=COLUMNS
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
            columns=COLUMNS
        )


# =========================================================
# SAVE WEEK
# =========================================================

def save_weekly_sheet(
    year: int,
    week: int,
    time_range_str: str,
    df_current: pd.DataFrame,
):
    """
    Lưu dữ liệu tuần vào Google Sheets.

    Return:
        True  -> thành công
        False -> thất bại
    """

    try:

        spreadsheet = get_spreadsheet()

        worksheet = get_or_create_worksheet(
            spreadsheet
        )


        data = worksheet.get_all_records()


        if data:

            df_all = pd.DataFrame(
                data
            )


            if "Năm" in df_all.columns:

                df_all["Năm"] = pd.to_numeric(
                    df_all["Năm"],
                    errors="coerce",
                )

            else:

                df_all["Năm"] = ""


            if "Tuần" in df_all.columns:

                df_all["Tuần"] = pd.to_numeric(
                    df_all["Tuần"],
                    errors="coerce",
                )

            else:

                df_all["Tuần"] = ""


            df_other = df_all[
                ~(
                    (
                        df_all["Năm"]
                        == year
                    )
                    &
                    (
                        df_all["Tuần"]
                        == week
                    )
                )
            ].copy()


            for column in SHEET_HEADERS:

                if column not in df_other.columns:

                    df_other[column] = (
                        False
                        if column == "Trạng thái"
                        else ""
                    )


            df_other = df_other[
                SHEET_HEADERS
            ]


        else:

            df_other = pd.DataFrame(
                columns=SHEET_HEADERS
            )


        # ---------------------------------------------
        # CURRENT WEEK DATA
        # ---------------------------------------------

        df_save = normalize_dataframe(
            df_current
        )


        df_save.insert(
            0,
            "Năm",
            int(year),
        )


        df_save.insert(
            1,
            "Tuần",
            int(week),
        )


        df_save.insert(
            2,
            "Mốc thời gian",
            str(time_range_str),
        )


        # ---------------------------------------------
        # MERGE
        # ---------------------------------------------

        df_final = pd.concat(
            [
                df_other,
                df_save,
            ],
            ignore_index=True,
        )


        df_final = df_final[
            SHEET_HEADERS
        ]


        df_final = df_final.fillna("")


        # ---------------------------------------------
        # CONVERT TO PLAIN PYTHON TYPES
        # ---------------------------------------------

        rows = []


        for row in df_final.itertuples(
            index=False,
            name=None,
        ):

            clean_row = []


            for value in row:

                if isinstance(
                    value,
                    bool,
                ):

                    clean_row.append(
                        bool(value)
                    )

                elif hasattr(
                    value,
                    "item",
                ):

                    try:

                        clean_row.append(
                            value.item()
                        )

                    except Exception:

                        clean_row.append(
                            value
                        )

                else:

                    clean_row.append(
                        value
                    )


            rows.append(
                clean_row
            )


        # ---------------------------------------------
        # WRITE
        # ---------------------------------------------

        worksheet.clear()


        data_to_write = [
            SHEET_HEADERS
        ] + rows


        worksheet.update(
            range_name="A1",
            values=data_to_write,
        )


        return True


    except gspread.exceptions.APIError:

        return False


    except Exception as e:

        st.error(
            f"Lỗi khi lưu Google Sheets: "
            f"{type(e).__name__}"
        )

        st.code(
            repr(e)
        )

        return False
