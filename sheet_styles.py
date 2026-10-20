"""Định dạng hai tab bằng Google Sheets batchUpdate."""

def color(hex_code):
    return {name: int(hex_code[i:i+2], 16) / 255 for name, i in [('red', 1), ('green', 3), ('blue', 5)]}


def style_sheet(sheet, row_count, column_count, performance=False):
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

    iso_year = 'YEAR(TODAY()-WEEKDAY(TODAY(),2)+4)'
    iso_week = 'WEEKNUM(TODAY(),21)'
    if performance:
        current = f'$A2=TEXT({iso_year},"0000")&"-W"&TEXT({iso_week},"00")'
        rules = [
            (f'AND({current},$B2=100)', '#F0AD4E', '#D1E7DD'),
            (current, '#F0AD4E', None),
        ]
        # Chỉ tô ô kết quả; dòng tuần vẫn giữ màu chữ theo tuần.
        assessment_range = dict(body, startColumnIndex=4, endColumnIndex=5)
        score_rules = [
            ('AND(ISNUMBER($B2),$B2<40)', '#842029', '#F8D7DA'),
            ('AND(ISNUMBER($B2),$B2>=40,$B2<80)', '#C65911', None),
            ('AND(ISNUMBER($B2),$B2>=80)', '#198754', '#D1E7DD'),
        ]
    else:
        current = f'AND($B2={iso_year},$C2={iso_week})'
        backlog = f'AND($E2<>"",$J2="",$B2*100+$C2<{iso_year}*100+{iso_week})'
        complete = '$K2="Hoàn thành đúng tiến độ"'
        rules = [
            ('$K2="Hoàn thành trễ"', '#842029', '#F8D7DA'),
            (backlog, '#C65911', None),
            (f'AND({current},{complete})', '#F0AD4E', '#D1E7DD'),
            (current, '#F0AD4E', None),
            (complete, '#198754', '#D1E7DD'),
        ]
        score_rules = []
        requests.append({'updateDimensionProperties': {'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5},
                                                       'properties': {'pixelSize': 320}, 'fields': 'pixelSize'}})
    ordered = [(formula, fg, bg, assessment_range) for formula, fg, bg in score_rules]
    ordered += [(formula, fg, bg, body) for formula, fg, bg in rules]
    for index, (formula, fg, bg, target) in enumerate(ordered):
        fmt = {'textFormat': {'foregroundColor': color(fg)}}
        if bg:
            fmt['backgroundColor'] = color(bg)
        requests.append({'addConditionalFormatRule': {'index': index, 'rule': {
            'ranges': [target], 'booleanRule': {'condition': {'type': 'CUSTOM_FORMULA', 'values': [{'userEnteredValue': '='+formula}]},
                                               'format': fmt}}}})
    sheet.spreadsheet.batch_update({'requests': requests})
