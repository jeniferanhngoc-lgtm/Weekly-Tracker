import gspread
import pandas as pd
import streamlit as st

COLUMNS = ["Tên công việc", "Mức độ ưu tiên", "Deadline", "Trạng thái"]


def get_spreadsheet():
    """Kết nối tới Google Spreadsheet."""
    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    return gc.open_by_key(spreadsheet_id)


def get_or_create_worksheet(sh):
    """Lấy worksheet Simple_Weekly_Tasks hoặc tạo mới nếu chưa tồn tại."""
    try:
        worksheet = sh.worksheet("Simple_Weekly_Tasks")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(
            title="Simple_Weekly_Tasks",
            rows="500",
            cols="10"
        )
        worksheet.append_row(
            ["Năm", "Tuần", "Mốc thời gian"] + COLUMNS
        )

    return worksheet


def load_weekly_sheet(year: int, week: int):
    """Tải danh sách công việc của tuần được chọn từ Google Sheets."""
    try:
        sh = get_spreadsheet()
        worksheet = get_or_create_worksheet(sh)

        data = worksheet.get_all_records()

        if not data:
            return pd.DataFrame(columns=COLUMNS)

        df_all = pd.DataFrame(data)

        # Ép kiểu để tránh trường hợp Google Sheets trả về chuỗi
        if "Năm" in df_all.columns:
            df_all["Năm"] = pd.to_numeric(
                df_all["Năm"],
                errors="coerce"
            )

        if "Tuần" in df_all.columns:
            df_all["Tuần"] = pd.to_numeric(
                df_all["Tuần"],
                errors="coerce"
            )

        df_filtered = df_all[
            (df_all["Năm"] == year) &
            (df_all["Tuần"] == week)
        ].copy()

        if df_filtered.empty:
            return pd.DataFrame(columns=COLUMNS)

        # Đồng bộ dữ liệu cũ
        if "Trạng thái" in df_filtered.columns:
            df_filtered["Trạng thái"] = df_filtered["Trạng thái"].apply(
                lambda x: str(x).strip().lower()
                in ["true", "1", "x", "hoàn thành"]
            )

        elif "Đã xong" in df_filtered.columns:
            df_filtered["Trạng thái"] = df_filtered["Đã xong"].apply(
                lambda x: str(x).strip().lower()
                in ["true", "1", "x", "hoàn thành"]
            )

        else:
            df_filtered["Trạng thái"] = False

        # Đảm bảo đủ các cột cần thiết
        for col in COLUMNS:
            if col not in df_filtered.columns:
                df_filtered[col] = False if col == "Trạng thái" else ""

        return df_filtered[COLUMNS]

    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu Google Sheets: {e}")
        return pd.DataFrame(columns=COLUMNS)


def save_weekly_sheet(
    year: int,
    week: int,
    time_range_str: str,
    df_current: pd.DataFrame
):
    """Lưu danh sách công việc của tuần vào Google Sheets."""

    try:
        sh = get_spreadsheet()
        worksheet = get_or_create_worksheet(sh)

        data = worksheet.get_all_records()

        if data:
            df_all = pd.DataFrame(data)

            # Ép kiểu Năm/Tuần
            if "Năm" in df_all.columns:
                df_all["Năm"] = pd.to_numeric(
                    df_all["Năm"],
                    errors="coerce"
                )

            if "Tuần" in df_all.columns:
                df_all["Tuần"] = pd.to_numeric(
                    df_all["Tuần"],
                    errors="coerce"
                )

            # Giữ lại dữ liệu của các tuần khác
            df_other = df_all[
                ~(
                    (df_all["Năm"] == year) &
                    (df_all["Tuần"] == week)
                )
            ].copy()

        else:
            df_other = pd.DataFrame(
                columns=["Năm", "Tuần", "Mốc thời gian"] + COLUMNS
            )

        # Chuẩn bị dữ liệu tuần hiện tại
        df_save = df_current.copy()

        for col in COLUMNS:
            if col not in df_save.columns:
                df_save[col] = False if col == "Trạng thái" else ""

        df_save = df_save[COLUMNS]

        df_save.insert(0, "Năm", year)
        df_save.insert(1, "Tuần", week)
        df_save.insert(2, "Mốc thời gian", time_range_str)

        # Ghép dữ liệu cũ + tuần hiện tại
        df_final = pd.concat(
            [df_other, df_save],
            ignore_index=True
        )

        # Thay NaN bằng chuỗi rỗng để gspread không nổi cáu
        df_final = df_final.fillna("")

        worksheet.clear()

        data_to_write = (
            [df_final.columns.tolist()]
            + df_final.values.tolist()
        )

        worksheet.update(
            range_name="A1",
            values=data_to_write
        )

    except Exception as e:
        st.error(f"Lỗi khi lưu dữ liệu Google Sheets: {e}")
        raise

