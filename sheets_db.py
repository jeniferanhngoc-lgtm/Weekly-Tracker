import gspread
import pandas as pd
import streamlit as st


# =========================================================
# CẤU HÌNH
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
# KẾT NỐI GOOGLE SHEETS
# =========================================================

def get_spreadsheet():
    """
    Đăng nhập bằng Google Service Account
    và mở Spreadsheet theo ID.
    """

    spreadsheet_id = str(
        st.secrets["spreadsheet_id"]
    ).strip()

    service_account_info = dict(
        st.secrets["gcp_service_account"]
    )

    gc = gspread.service_account_from_dict(
        service_account_info
    )

    return gc.open_by_key(
        spreadsheet_id
    )


# =========================================================
# LẤY / TẠO WORKSHEET
# =========================================================

def get_or_create_worksheet(spreadsheet):
    """
    Lấy worksheet Simple_Weekly_Tasks.

    Nếu chưa tồn tại thì tự động tạo.
    """

    try:

        worksheet = spreadsheet.worksheet(
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
# CHUẨN HÓA TRẠNG THÁI
# =========================================================

def parse_status(value):
    """
    Chuyển dữ liệu từ Google Sheets
    về True / False.
    """

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
        "da hoan thanh",
        "đã hoàn thành",
    ]


# =========================================================
# CHUẨN HÓA DATAFRAME
# =========================================================

def normalize_dataframe(df):
    """
    Đảm bảo DataFrame luôn có đúng cấu trúc.
    """

    if df is None:
        return pd.DataFrame(
            columns=COLUMNS
        )

    df = df.copy()

    # Hỗ trợ dữ liệu phiên bản cũ
    if (
        "Trạng thái" not in df.columns
        and "Đã xong" in df.columns
    ):

        df["Trạng thái"] = df[
            "Đã xong"
        ].apply(parse_status)


    for column in COLUMNS:

        if column not in df.columns:

            if column == "Trạng thái":
                df[column] = False

            else:
                df[column] = ""


    df["Trạng thái"] = (
        df["Trạng thái"]
        .apply(parse_status)
    )


    return df[COLUMNS]


# =========================================================
# LOAD DỮ LIỆU TUẦN
# =========================================================

def load_weekly_sheet(
    year: int,
    week: int,
):
    """
    Tải danh sách công việc của
    năm / tuần được chọn.
    """

    try:

        # ---------------------------------------------
        # Kết nối Spreadsheet
        # ---------------------------------------------

        spreadsheet = get_spreadsheet()

        worksheet = get_or_create_worksheet(
            spreadsheet
        )


        # ---------------------------------------------
        # Đọc dữ liệu
        # ---------------------------------------------

        data = worksheet.get_all_records()


        if not data:

            return pd.DataFrame(
                columns=COLUMNS
            )


        df_all = pd.DataFrame(data)


        # ---------------------------------------------
        # Kiểm tra cấu trúc
        # ---------------------------------------------

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


        # ---------------------------------------------
        # Ép kiểu
        # ---------------------------------------------

        df_all["Năm"] = pd.to_numeric(
            df_all["Năm"],
            errors="coerce",
        )


        df_all["Tuần"] = pd.to_numeric(
            df_all["Tuần"],
            errors="coerce",
        )


        # ---------------------------------------------
        # Lọc theo tuần
        # ---------------------------------------------

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


        # ---------------------------------------------
        # Hỗ trợ cột phiên bản cũ
        # ---------------------------------------------

        if (
            "Trạng thái"
            not in df_filtered.columns
            and
            "Đã xong"
            in df_filtered.columns
        ):

            df_filtered[
                "Trạng thái"
            ] = df_filtered[
                "Đã xong"
            ]


        # ---------------------------------------------
        # Chuẩn hóa
        # ---------------------------------------------

        return normalize_dataframe(
            df_filtered
        )


    # =====================================================
    # LỖI KHÔNG CÓ QUYỀN
    # =====================================================

    except PermissionError:

        service_email = str(
            st.secrets[
                "gcp_service_account"
            ][
                "client_email"
            ]
        )


        spreadsheet_id = str(
            st.secrets[
                "spreadsheet_id"
            ]
        )


        st.error(
            "Google trả về lỗi 403 Permission Denied."
        )


        st.warning(
            "Google Service Account đăng nhập được, "
            "nhưng không mở được Spreadsheet."
        )


        st.code(
            f"""Service account đang dùng:
{service_email}

Spreadsheet ID đang dùng:
{spreadsheet_id}"""
        )


        st.info(
            "Hãy kiểm tra Google Sheet đã được "
            "Share cho đúng service account phía trên "
            "với quyền Editor hay chưa."
        )


        return pd.DataFrame(
            columns=COLUMNS
        )


    # =====================================================
    # KHÔNG TÌM THẤY SPREADSHEET
    # =====================================================

    except gspread.exceptions.SpreadsheetNotFound:

        st.error(
            "Không tìm thấy Google Spreadsheet."
        )


        st.code(
            f'Spreadsheet ID: '
            f'{st.secrets["spreadsheet_id"]}'
        )


        return pd.DataFrame(
            columns=COLUMNS
        )


    # =====================================================
    # LỖI API
    # =====================================================

    except gspread.exceptions.APIError as e:

        st.error(
            "Google Sheets API trả về lỗi."
        )


        st.code(
            repr(e)
        )


        return pd.DataFrame(
            columns=COLUMNS
        )


    # =====================================================
    # LỖI KHÁC
    # =====================================================

    except Exception as e:

        st.error(
            f"Lỗi kết nối Google Sheets: "
            f"{type(e).__name__}"
        )


        st.code(
            repr(e)
        )


        return pd.DataFrame(
            columns=COLUMNS
        )


# =========================================================
# LƯU DỮ LIỆU TUẦN
# =========================================================

def save_weekly_sheet(
    year: int,
    week: int,
    time_range_str: str,
    df_current: pd.DataFrame,
):
    """
    Lưu / cập nhật dữ liệu tuần lên Google Sheets.

    Trả về:
        True  -> lưu thành công
        False -> lưu thất bại
    """

    try:

        # ---------------------------------------------
        # Kết nối
        # ---------------------------------------------

        spreadsheet = get_spreadsheet()

        worksheet = get_or_create_worksheet(
            spreadsheet
        )


        # ---------------------------------------------
        # Đọc toàn bộ dữ liệu cũ
        # ---------------------------------------------

        data = worksheet.get_all_records()


        if data:

            df_all = pd.DataFrame(data)


            # -----------------------------------------
            # Chuẩn hóa năm / tuần
            # -----------------------------------------

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


            # -----------------------------------------
            # Xóa dữ liệu cũ của tuần hiện tại
            # -----------------------------------------

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


            # Chuẩn hóa dữ liệu cũ
            for column in SHEET_HEADERS:

                if column not in df_other.columns:

                    if column == "Trạng thái":
                        df_other[column] = False

                    else:
                        df_other[column] = ""


            df_other = df_other[
                SHEET_HEADERS
            ]


        else:

            df_other = pd.DataFrame(
                columns=SHEET_HEADERS
            )


        # ---------------------------------------------
        # Chuẩn bị dữ liệu tuần hiện tại
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
        # Ghép dữ liệu
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


        # ---------------------------------------------
        # Làm sạch NaN
        # ---------------------------------------------

        df_final = df_final.fillna("")


        # ---------------------------------------------
        # Chuyển numpy type thành Python type
        # để JSON của Google không giận dữ
        # ---------------------------------------------

        rows = []


        for row in df_final.itertuples(
            index=False,
            name=None,
        ):

            clean_row = []

            for value in row:

                # Boolean
                if isinstance(
                    value,
                    (bool,),
                ):

                    clean_row.append(
                        bool(value)
                    )

                # Number
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
        # Ghi lại Sheet
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


    # =====================================================
    # LỖI QUYỀN
    # =====================================================

    except PermissionError:

        service_email = str(
            st.secrets[
                "gcp_service_account"
            ][
                "client_email"
            ]
        )


        spreadsheet_id = str(
            st.secrets[
                "spreadsheet_id"
            ]
        )


        st.error(
            "Không có quyền truy cập Google Sheet."
        )


        st.code(
            f"""Service account:
{service_email}

Spreadsheet ID:
{spreadsheet_id}"""
        )


        st.info(
            "Hãy Share đúng Google Sheet cho "
            "service account phía trên "
            "với quyền Editor."
        )


        return False


    # =====================================================
    # KHÔNG TÌM THẤY SPREADSHEET
    # =====================================================

    except gspread.exceptions.SpreadsheetNotFound:

        st.error(
            "Không tìm thấy Google Spreadsheet."
        )


        st.code(
            f'Spreadsheet ID: '
            f'{st.secrets["spreadsheet_id"]}'
        )


        return False


    # =====================================================
    # API ERROR
    # =====================================================

    except gspread.exceptions.APIError as e:

        st.error(
            "Google Sheets API trả về lỗi."
        )


        st.code(
            repr(e)
        )


        return False


    # =====================================================
    # LỖI KHÁC
    # =====================================================

    except Exception as e:

        st.error(
            f"Lỗi khi lưu Google Sheets: "
            f"{type(e).__name__}"
        )


        st.code(
            repr(e)
        )


        return False
