"""Định dạng hai tab bằng Google Sheets batchUpdate."""

def color(hex_code):
    return {name: int(hex_code[i:i+2], 16) / 255 for name, i in [('red', 1), ('green', 3), ('blue', 5)]}


def style_sheet(sheet, row_count, column_count, performance=False, today=None):
    # Gọi sau khi ghi: chỉ cắt phần dòng trống, giữ toàn bộ dữ liệu vừa xác nhận.
    sheet.resize(rows=max(2, row_count))
    sid = sheet.id
    body = {'sheetId': sid, 'startRowIndex': 1, 'endRowIndex': max(2, row_count),
            'startColumnIndex': 0, 'endColumnIndex': column_count}
    header = dict(body, startRowIndex=0, endRowIndex=1)
    requests = [
        {'repeatCell': {'range': body, 'cell': {'userEnteredFormat': {
            'backgroundColor': color('#F8F9FA'), 'textFormat': {'foregroundColor': color('#000000')},
            'verticalAlignment': 'MIDDLE', 'wrapStrategy': 'WRAP'}}, 'fields': 'userEnteredFormat'}},
        {'repeatCell': {'range': header, 'cell': {'userEnteredFormat': {
            'backgroundColor': color('#0F5132'), 'textFormat': {'foregroundColor': color('#FFFFFF'), 'bold': True},
            'verticalAlignment': 'MIDDLE', 'wrapStrategy': 'WRAP'}}, 'fields': 'userEnteredFormat'}},
        {'updateSheetProperties': {'properties': {'sheetId': sid, 'gridProperties': {'frozenRowCount': 1}},
                                   'fields': 'gridProperties.frozenRowCount'}},
        {'updateDimensionProperties': {'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': column_count},
                                       'properties': {'pixelSize': 170}, 'fields': 'pixelSize'}},
    ]
    # Thay bộ quy tắc để mỗi lần lưu không nhân đôi conditional formatting.
    metadata = sheet.spreadsheet.fetch_sheet_metadata()
    existing = next(s for s in metadata['sheets'] if s['properties']['sheetId'] == sid)
    for index in reversed(range(len(existing.get('conditionalFormats', [])))):
        requests.append({'deleteConditionalFormatRule': {'sheetId': sid, 'index': index}})

    # Tô trực tiếp: không dùng công thức phụ thuộc locale của bảng tính.
    import datetime
    from zoneinfo import ZoneInfo
    now = today or datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    year, week, _ = now.isocalendar()
    current_key = f"{year}-W{week:02d}"
    values = sheet.get_all_values(value_render_option="UNFORMATTED_VALUE")

    def paint(row_index, fg, bg=None, start=0, end=None):
        target = dict(body, startRowIndex=row_index, endRowIndex=row_index+1,
                      startColumnIndex=start, endColumnIndex=end or column_count)
        fmt = {'textFormat': {'foregroundColor': color(fg)}}
        fields = 'userEnteredFormat.textFormat.foregroundColor'
        if bg:
            fmt['backgroundColor'] = color(bg)
            fields += ',userEnteredFormat.backgroundColor'
        requests.append({'repeatCell': {'range': target, 'cell': {'userEnteredFormat': fmt}, 'fields': fields}})

    for index, raw in enumerate(values[1:row_count], start=1):
        row = list(raw) + [''] * max(0, column_count-len(raw))
        if performance:
            current = row[0] == current_key
            if current:
                paint(index, '#F0AD4E')
            score = row[1]
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                if score < 40:
                    paint(index, '#842029', '#F8D7DA', 4, 5)
                elif score < 80:
                    paint(index, '#C65911', start=4, end=5)
                else:
                    paint(index, '#198754', '#D1E7DD', 4, 5)
                    if current and score == 100:
                        paint(index, '#F0AD4E', '#D1E7DD', 0, 4)
                        paint(index, '#F0AD4E', '#D1E7DD', 5, column_count)
        else:
            try:
                origin = int(row[1]), int(row[2])
            except (ValueError, TypeError):
                origin = None
            current = origin == (year, week)
            backlog = bool(str(row[4]).strip()) and row[9] == '' and origin is not None and origin < (year, week)
            if row[10] == 'Hoàn thành trễ':
                paint(index, '#842029', '#F8D7DA')
            elif backlog:
                paint(index, '#C65911')
            elif row[10] == 'Hoàn thành đúng tiến độ':
                paint(index, '#F0AD4E' if current else '#198754', '#D1E7DD')
            elif current:
                paint(index, '#F0AD4E')
    if not performance:
        requests.append({'updateDimensionProperties': {'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5},
                                                       'properties': {'pixelSize': 320}, 'fields': 'pixelSize'}})
    sheet.spreadsheet.batch_update({'requests': requests})
