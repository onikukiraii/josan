import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from entity.enums import ShiftType

SHIFT_TYPE_LABELS: dict[ShiftType, str] = {
    ShiftType.outpatient_leader: "外来L",
    ShiftType.treatment_room: "処置室",
    ShiftType.beauty: "美容",
    ShiftType.mw_outpatient: "MW外来",
    ShiftType.ward_leader: "病棟L",
    ShiftType.ward: "病棟",
    ShiftType.delivery: "分娩",
    ShiftType.delivery_charge: "分娩担当",
    ShiftType.night_leader: "夜勤L",
    ShiftType.night: "夜勤",
}

DISPLAY_SHIFT_TYPES = [
    ShiftType.outpatient_leader,
    ShiftType.treatment_room,
    ShiftType.beauty,
    ShiftType.mw_outpatient,
    ShiftType.ward_leader,
    ShiftType.ward,
    ShiftType.delivery,
    ShiftType.delivery_charge,
    ShiftType.night_leader,
    ShiftType.night,
]

WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
FONT_NAME = "HeiseiKakuGo-W5"


def generate_schedule_pdf(
    year_month: str,
    assignments: list[dict[str, object]],
) -> BytesIO:
    """シフト表をPDFとして生成する。

    assignments: [{"member_name": str, "date": date, "shift_type": ShiftType}, ...]
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontName = FONT_NAME
    title_style.fontSize = 14

    year, month = year_month.split("-")
    title = Paragraph(f"{year}年{month}月 シフト表", title_style)

    # 日付→シフト種別→メンバー名のマッピングを作成
    date_shift_map: dict[str, dict[ShiftType, list[str]]] = {}
    for a in assignments:
        ds = str(a["date"])
        st = a["shift_type"]
        name = str(a["member_name"])
        if st == ShiftType.day_off:
            continue
        date_shift_map.setdefault(ds, {}).setdefault(st, []).append(name)

    # 日付リストを作成
    import calendar

    y, m = int(year), int(month)
    _, last_day = calendar.monthrange(y, m)
    all_dates = [datetime.date(y, m, d) for d in range(1, last_day + 1)]

    # テーブルヘッダー
    header = ["日付", "曜日"] + [SHIFT_TYPE_LABELS[s] for s in DISPLAY_SHIFT_TYPES]

    # テーブルデータ
    table_data = [header]
    for d in all_dates:
        ds = str(d)
        weekday = WEEKDAY_JP[d.weekday()]
        row = [f"{d.day}", weekday]
        for st in DISPLAY_SHIFT_TYPES:
            names = date_shift_map.get(ds, {}).get(st, [])
            row.append("\n".join(names))
        table_data.append(row)

    # カラム幅
    col_widths = [25 * mm, 12 * mm] + [22 * mm] * len(DISPLAY_SHIFT_TYPES)

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEADING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    # 土曜・日祝の行に背景色
    for i, d in enumerate(all_dates, start=1):
        if d.weekday() == 5:
            table.setStyle(TableStyle([("BACKGROUND", (1, i), (1, i), colors.HexColor("#CCE5FF"))]))
        elif d.weekday() == 6:
            table.setStyle(TableStyle([("BACKGROUND", (1, i), (1, i), colors.HexColor("#FFCCCC"))]))

    elements = [title, Spacer(1, 5 * mm), table]
    doc.build(elements)
    buffer.seek(0)
    return buffer
