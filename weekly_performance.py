"""Các phép tính thống kê theo tuần ISO, không phụ thuộc Streamlit."""
import datetime
from zoneinfo import ZoneInfo
import pandas as pd

STATUS_COLUMN = 'Đánh giá tiến độ'
PERFORMANCE_SHEET = 'Weekly_Performance'
PERFORMANCE_HEADERS = ['Tuần', 'Hoàn thành (%)', 'Việc tồn đầu tuần', 'Xử lý việc tồn', 'Đánh giá', 'Task tuần', 'Hoàn thành đúng tuần']


def week_bounds(year, week):
    start = pd.Timestamp(datetime.date.fromisocalendar(int(year), int(week), 1))
    return start, start + pd.Timedelta(days=7)


def classification(row, today=None):
    """Phân loại tính theo tuần gốc; tuần chưa kết thúc là 'Đang thực hiện'."""
    try:
        origin, end = week_bounds(row['Năm gốc'], row['Tuần gốc'])
    except (ValueError, TypeError, KeyError):
        return 'Chưa rõ tuần gốc'
    done = pd.to_datetime(row.get('Ngày hoàn thành'), errors='coerce')
    if pd.notna(done):
        return 'Hoàn thành đúng tiến độ' if origin <= done < end else 'Hoàn thành trễ'
    now = pd.Timestamp(today if today is not None else datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None))
    return 'Chưa hoàn thành' if now < end else 'Việc tồn'


def week_summary(df, year, week):
    """Tồn đầu tuần: mọi task từ tuần trước chưa xong lúc 00:00 thứ Hai.
    Task gốc của tuần tính đúng hạn chỉ khi completion nằm trong chính tuần.
    """
    start, end = week_bounds(year, week)
    assigned = on_time = backlog = resolved = 0
    for _, r in df.iterrows():
        if not str(r.get('Tên công việc', '')).strip():
            continue
        try:
            origin, _ = week_bounds(r['Năm gốc'], r['Tuần gốc'])
        except (ValueError, TypeError, KeyError):
            continue
        completed = pd.to_datetime(r.get('Ngày hoàn thành'), errors='coerce')
        if origin == start:
            assigned += 1
            if pd.notna(completed) and start <= completed < end:
                on_time += 1
        elif origin < start and (pd.isna(completed) or completed >= start):
            backlog += 1
            if pd.notna(completed) and start <= completed < end:
                resolved += 1
    percent = 100 * on_time / assigned if assigned else None
    if percent is None:
        assessment = 'N/A'
    elif percent == 100:
        assessment = 'Tuyệt vời'
    elif percent >= 80:
        assessment = 'Xuất sắc'
    elif percent >= 60:
        assessment = 'Hoàn thành tốt'
    elif percent >= 40:
        assessment = 'Cần sắp xếp lại công việc'
    else:
        assessment = 'Không hoàn thành tiến độ'
    return {'Tuần': f'{year}-W{week:02d}', 'Hoàn thành (%)': round(percent, 1) if percent is not None else 'N/A',
            'Việc tồn đầu tuần': backlog, 'Xử lý việc tồn': resolved, 'Đánh giá': assessment,
            'Task tuần': assigned, 'Hoàn thành đúng tuần': on_time}


def summary_table(df, today=None):
    today = pd.Timestamp(today if today is not None else datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date())
    current_year, current_week, _ = today.isocalendar()
    earliest = None
    for _, r in df.iterrows():
        try:
            origin, _ = week_bounds(r['Năm gốc'], r['Tuần gốc'])
            earliest = min(earliest, origin) if earliest is not None else origin
        except (ValueError, TypeError, KeyError):
            continue
    if earliest is None:
        earliest = week_bounds(current_year, current_week)[0]
    current = week_bounds(current_year, current_week)[0]
    rows = []
    while earliest <= current:
        y, w, _ = earliest.isocalendar()
        rows.append(week_summary(df, int(y), int(w)))
        earliest += pd.Timedelta(days=7)
    return pd.DataFrame(rows, columns=PERFORMANCE_HEADERS)
