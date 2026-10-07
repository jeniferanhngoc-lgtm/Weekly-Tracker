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
    "Ghi chú",
    "Trạng thái",
]


SHEET_HEADERS = [
    "Năm",
    "Tuần",
    "Mốc thời gian",
] + COLUMNS


WORKSHEET_NAME = "Simple_Weekly_Tasks"


# =========================================================
# GOOGLE CLIENT
# =========================================================

def get_google_client():

    service_account_info = dict(
        st.secrets[
            "gcp_service_account"
        ]
    )

    return gspread.service_account_from_dict(
        service_account_info
    )


# =========================================================
# SPREADSHEET
# =========================================================

def get_spreadsheet():

    spreadsheet_id = str(
        st.secrets[
            "spreadsheet_id"
        ]
    ).strip()


    service_account_info = dict(
        st.secrets[
            "gcp_service_account"
        ]
    )


    gc = get_google_client()


    try:

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

    try:

        worksheet = (
            spreadsheet.worksheet(
                WORKSHEET_NAME
            )
        )


    except gspread.exceptions.WorksheetNotFound:

        worksheet = (
            spreadsheet.add_worksheet(
                title=WORKSHEET_NAME,
                rows=500,
                cols=12,
            )
        )


        worksheet.append_row(
            SHEET_HEADERS
        )


    return worksheet


# =========================================================
# STATUS
# =========================================================

def parse_status(value):

    if isinstance(
        value,
        bool,
    ):
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
# DEADLINE
# =========================================================

def parse_deadline(value):
    """
    Chuyển deadline từ Google Sheets
    về pandas datetime.
    """

    if value is None:
        return pd.NaT


    text = str(
        value
    ).strip()


    if (
        text == ""
        or text.lower()
        in [
            "nan",
            "nat",
            "none",
        ]
    ):
        return pd.NaT


    return pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=True,
    )


# =========================================================
# NORMALIZE DATAFRAME
# =========================================================

def normalize_dataframe(df):

    if df is None:

        return pd.DataFrame(
            columns=COLUMNS
        )


    df = df.copy()


    # Hỗ trợ dữ liệu cũ
    if (
        "Trạng thái"
        not in df.columns
        and
        "Đã xong"
        in df.columns
    ):

        df[
            "Trạng thái"
        ] = df[
            "Đã xong"
        ]


    for column in COLUMNS:

        if column not in df.columns:

            if column == "Trạng thái":

                df[column] = False

            elif column == "Deadline":

                df[column] = pd.NaT

            else:

                df[column] = ""


    df[
        "Trạng thái"
    ] = (
        df[
            "Trạng thái"
        ]
        .apply(
            parse_status
        )
    )


    df[
        "Deadline"
    ] = (
        df[
            "Deadline"
        ]
        .apply(
            parse_deadline
        )
    )


    return df[
        COLUMNS
    ]


# =========================================================
# LOAD WEEK
# =========================================================

def load_weekly_sheet(
    year: int,
    week: int,
):

    try:

        spreadsheet = (
            get_spreadsheet()
        )


        worksheet = (
            get_or_create_worksheet(
                spreadsheet
            )
        )


        data = (
            worksheet.get_all_records()
        )


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


        df_all["Năm"] = (
            pd.to_numeric(
                df_all["Năm"],
                errors="coerce",
            )
        )


        df_all["Tuần"] = (
            pd.to_numeric(
                df_all["Tuần"],
                errors="coerce",
            )
        )


        df_filtered = df_all[
            (
                df_all["Năm"]
                == year
            )
            &
            (
                df_all["Tuần"]
                == week
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

    try:

        spreadsheet = (
            get_spreadsheet()
        )


        worksheet = (
            get_or_create_worksheet(
                spreadsheet
            )
        )


        data = (
            worksheet.get_all_records()
        )


        # =================================================
        # OLD DATA
        # =================================================

        if data:

            df_all = pd.DataFrame(
                data
            )


            if "Năm" in df_all.columns:

                df_all[
                    "Năm"
                ] = pd.to_numeric(
                    df_all["Năm"],
                    errors="coerce",
                )

            else:

                df_all[
                    "Năm"
                ] = ""


            if "Tuần" in df_all.columns:

                df_all[
                    "Tuần"
                ] = pd.to_numeric(
                    df_all["Tuần"],
                    errors="coerce",
                )

            else:

                df_all[
                    "Tuần"
                ] = ""


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


            # Đảm bảo dữ liệu cũ có Ghi chú
            for column in SHEET_HEADERS:

                if column not in df_other.columns:

                    if column == "Trạng thái":

                        df_other[
                            column
                        ] = False

                    else:

                        df_other[
                            column
                        ] = ""


            df_other = df_other[
                SHEET_HEADERS
            ]


        else:

            df_other = pd.DataFrame(
                columns=SHEET_HEADERS
            )


        # =================================================
        # CURRENT WEEK
        # =================================================

        df_save = normalize_dataframe(
            df_current
        )


        # Chuyển deadline thành text
        # để lưu Google Sheets ổn định
        df_save[
            "Deadline"
        ] = (
            df_save[
                "Deadline"
            ]
            .apply(
                lambda x:
                x.strftime(
                    "%d/%m/%Y %H:%M"
                )
                if pd.notna(x)
                else ""
            )
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
            str(
                time_range_str
            ),
        )


        # =================================================
        # MERGE
        # =================================================

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


        df_final = (
            df_final.fillna("")
        )


        # =================================================
        # CLEAN PYTHON TYPES
        # =================================================

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


                elif isinstance(
                    value,
                    pd.Timestamp,
                ):

                    clean_row.append(
                        value.strftime(
                            "%d/%m/%Y %H:%M"
                        )
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
                            str(value)
                        )


                else:

                    clean_row.append(
                        value
                    )


            rows.append(
                clean_row
            )


        # =================================================
        # WRITE
        # =================================================

        worksheet.clear()


        worksheet.update(
            range_name="A1",
            values=[
                SHEET_HEADERS
            ] + rows,
        )


        return True


    except gspread.exceptions.APIError as e:

        st.error(
            "Google Sheets API trả về lỗi."
        )

        st.code(
            repr(e)
        )

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
