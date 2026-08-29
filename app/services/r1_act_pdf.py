"""PDF renderer for Kazakhstan primary document form R-1.

The renderer accepts an immutable snapshot.  Persistence, authorization and
document status transitions live in the accounting route; keeping drawing here
makes the PDF easy to verify without a running database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass(frozen=True)
class R1ActPayload:
    act_number: str
    act_date: date
    work_date: date
    contractor_name: str
    contractor_iin: str
    service_name: str
    amount: Decimal
    receipt_number: str | None
    linked_request_ids: tuple[int, ...]
    customer_name: str
    customer_bin_iin: str
    customer_address: str
    customer_iik: str
    customer_bank_name: str
    customer_bik: str
    customer_kbe: str
    customer_director: str


_REGULAR_FONT_NAME = "ContrastR1Regular"
_BOLD_FONT_NAME = "ContrastR1Bold"


def _find_font(filename: str, env_name: str) -> str:
    configured = os.getenv(env_name)
    candidates = [
        configured,
        f"/usr/share/fonts/truetype/dejavu/{filename}",
        f"/usr/share/fonts/dejavu/{filename}",
        f"/usr/local/share/fonts/{filename}",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError(
        "Для формирования АВР не найден шрифт DejaVu Sans. "
        f"Укажите путь в {env_name}."
    )


def _register_fonts() -> tuple[str, str]:
    registered = set(pdfmetrics.getRegisteredFontNames())
    if _REGULAR_FONT_NAME not in registered:
        pdfmetrics.registerFont(
            TTFont(_REGULAR_FONT_NAME, _find_font("DejaVuSans.ttf", "R1_FONT_REGULAR_PATH"))
        )
    if _BOLD_FONT_NAME not in registered:
        pdfmetrics.registerFont(
            TTFont(_BOLD_FONT_NAME, _find_font("DejaVuSans-Bold.ttf", "R1_FONT_BOLD_PATH"))
        )
    return _REGULAR_FONT_NAME, _BOLD_FONT_NAME


_ONES_MALE = (
    "ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"
)
_ONES_FEMALE = (
    "ноль", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"
)
_TEENS = (
    "десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать",
    "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать",
)
_TENS = (
    "", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят",
    "семьдесят", "восемьдесят", "девяносто",
)
_HUNDREDS = (
    "", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот",
    "семьсот", "восемьсот", "девятьсот",
)


def _plural(value: int, one: str, few: str, many: str) -> str:
    last_two = value % 100
    if 11 <= last_two <= 14:
        return many
    last = value % 10
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


def _triplet_words(value: int, *, female: bool = False) -> list[str]:
    words: list[str] = []
    if value >= 100:
        words.append(_HUNDREDS[value // 100])
    remainder = value % 100
    if 10 <= remainder <= 19:
        words.append(_TEENS[remainder - 10])
        return words
    if remainder >= 20:
        words.append(_TENS[remainder // 10])
    ones = remainder % 10
    if ones:
        words.append((_ONES_FEMALE if female else _ONES_MALE)[ones])
    return words


def integer_to_russian_words(value: int) -> str:
    if value == 0:
        return "ноль"
    if value < 0 or value >= 1_000_000_000_000:
        return str(value)
    words: list[str] = []
    groups = (
        (1_000_000_000, False, ("миллиард", "миллиарда", "миллиардов")),
        (1_000_000, False, ("миллион", "миллиона", "миллионов")),
        (1_000, True, ("тысяча", "тысячи", "тысяч")),
    )
    remainder = value
    for divider, female, forms in groups:
        group = remainder // divider
        if group:
            words.extend(_triplet_words(group, female=female))
            words.append(_plural(group, *forms))
            remainder %= divider
    words.extend(_triplet_words(remainder))
    return " ".join(words)


def amount_in_words(value: Decimal) -> str:
    normalized = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tenge = int(normalized)
    tiyn = int((normalized - Decimal(tenge)) * 100)
    return (
        f"{integer_to_russian_words(tenge)} "
        f"{_plural(tenge, 'тенге', 'тенге', 'тенге')} {tiyn:02d} тиын"
    )


def _money(value: Decimal) -> str:
    normalized = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    whole, fraction = f"{normalized:.2f}".split(".")
    grouped = f"{int(whole):,}".replace(",", " ")
    return f"{grouped},{fraction}"


def _date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def _safe(value: object) -> str:
    text = str(value or "").strip()
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def generate_r1_act_pdf(payload: R1ActPayload) -> bytes:
    regular, bold = _register_fonts()
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    document = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=9 * mm,
        bottomMargin=9 * mm,
        title=f"АВР {payload.act_number}",
        author=payload.customer_name,
        subject="Акт выполненных работ (оказанных услуг), форма Р-1",
    )

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "R1Base",
        parent=styles["Normal"],
        fontName=regular,
        fontSize=7.4,
        leading=9.2,
        textColor=colors.HexColor("#111111"),
        spaceAfter=0,
    )
    small = ParagraphStyle("R1Small", parent=base, fontSize=6.2, leading=7.5)
    tiny = ParagraphStyle("R1Tiny", parent=base, fontSize=5.7, leading=6.8)
    bold_style = ParagraphStyle("R1Bold", parent=base, fontName=bold)
    center = ParagraphStyle("R1Center", parent=base, alignment=TA_CENTER)
    center_bold = ParagraphStyle("R1CenterBold", parent=center, fontName=bold)
    right_small = ParagraphStyle("R1RightSmall", parent=small, alignment=TA_RIGHT)
    title = ParagraphStyle(
        "R1Title",
        parent=center_bold,
        fontSize=11.5,
        leading=13.5,
        spaceAfter=0,
    )

    story: list[object] = []
    story.append(
        Paragraph(
            "Приложение 50 к приказу Министра финансов<br/>"
            "Республики Казахстан от 20 декабря 2012 года № 562<br/>"
            "<b>Форма Р-1</b>",
            right_small,
        )
    )
    story.append(Spacer(1, 2 * mm))

    customer_details = (
        f"<b>{_safe(payload.customer_name)}</b><br/>"
        f"{_safe(payload.customer_address)}<br/>"
        f"ИИК {_safe(payload.customer_iik)}, {_safe(payload.customer_bank_name)}, "
        f"БИК {_safe(payload.customer_bik)}, КБе {_safe(payload.customer_kbe)}"
    )
    contractor_details = (
        f"<b>{_safe(payload.contractor_name)}</b>, самозанятый"
    )
    basis = "Чек e-Salyq Business"
    if payload.receipt_number:
        basis += f" № {_safe(payload.receipt_number)}"
    basis += f" от {_date(payload.work_date)}"
    if payload.linked_request_ids:
        basis += "; заявки: " + ", ".join(f"№{value}" for value in payload.linked_request_ids)

    parties = Table(
        [
            [Paragraph("Заказчик", bold_style), Paragraph(customer_details, base), Paragraph("ИИН/БИН", bold_style), Paragraph(_safe(payload.customer_bin_iin), base)],
            [Paragraph("Исполнитель", bold_style), Paragraph(contractor_details, base), Paragraph("ИИН", bold_style), Paragraph(_safe(payload.contractor_iin), base)],
            [Paragraph("Договор<br/>(контракт)", bold_style), Paragraph(basis, base), "", ""],
        ],
        colWidths=[24 * mm, 158 * mm, 25 * mm, 40 * mm],
    )
    parties.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (1, 2), (3, 2)),
                ("LINEBELOW", (1, 0), (1, 2), 0.35, colors.HexColor("#777777")),
                ("LINEBELOW", (3, 0), (3, 1), 0.35, colors.HexColor("#777777")),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(parties)
    story.append(Spacer(1, 3 * mm))

    heading = Table(
        [[Paragraph("АКТ ВЫПОЛНЕННЫХ РАБОТ (ОКАЗАННЫХ УСЛУГ)", title), Paragraph("Номер документа", center_bold), Paragraph("Дата составления", center_bold)],
         ["", Paragraph(_safe(payload.act_number), center), Paragraph(_date(payload.act_date), center)]],
        colWidths=[171 * mm, 39 * mm, 37 * mm],
    )
    heading.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (0, 1)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (1, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (1, 0), (-1, -1), 0.35, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(heading)
    story.append(Spacer(1, 3 * mm))

    headers = [
        "Номер<br/>по порядку",
        "Наименование работ (услуг)",
        "Дата выполнения работ (оказания услуг)",
        "Сведения об отчете (при наличии)",
        "Единица измерения",
        "Количество",
        "Цена за единицу",
        "Стоимость",
    ]
    body_row = [
        "1",
        Paragraph(_safe(payload.service_name), base),
        _date(payload.work_date),
        "—",
        "услуга",
        "1",
        _money(payload.amount),
        _money(payload.amount),
    ]
    table_data = [
        [Paragraph(value, tiny) for value in headers],
        [Paragraph(str(index + 1), tiny) for index in range(8)],
        [Paragraph(str(value), base) if not hasattr(value, "wrap") else value for value in body_row],
        ["", Paragraph("Итого", bold_style), "", "", "", Paragraph("1", center), Paragraph("х", center), Paragraph(_money(payload.amount), bold_style)],
    ]
    works = Table(
        table_data,
        colWidths=[11 * mm, 78 * mm, 25 * mm, 42 * mm, 22 * mm, 18 * mm, 25 * mm, 26 * mm],
        repeatRows=2,
    )
    works.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#F2F4F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 2), (1, 2), "LEFT"),
                ("ALIGN", (7, 2), (7, -1), "RIGHT"),
                ("SPAN", (1, 3), (4, 3)),
                ("FONTNAME", (0, 0), (-1, 1), bold),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(works)
    story.append(Spacer(1, 3 * mm))

    details = [
        Paragraph(f"<b>В том числе НДС:</b> без НДС.", base),
        Paragraph(f"<b>Всего на сумму:</b> {_safe(amount_in_words(payload.amount).capitalize())}.", base),
        Paragraph("<b>Сведения об использовании запасов, полученных от заказчика:</b> запасы не передавались.", base),
        Paragraph(
            "<b>Приложение:</b> чек e-Salyq Business"
            + (f" № {_safe(payload.receipt_number)}" if payload.receipt_number else "")
            + " на 1 странице.",
            base,
        ),
    ]
    story.extend([item for pair in ((item, Spacer(1, 1.3 * mm)) for item in details) for item in pair])

    signatures = Table(
        [
            [Paragraph("Сдал (Исполнитель)", bold_style), Paragraph("Принял (Заказчик)", bold_style)],
            [
                Paragraph(f"Самозанятый&nbsp;&nbsp; /____________/ {_safe(payload.contractor_name)}", base),
                Paragraph(f"Директор&nbsp;&nbsp; /____________/ {_safe(payload.customer_director)}", base),
            ],
            [Paragraph("должность&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; подпись&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; расшифровка подписи", tiny),
             Paragraph("должность&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; подпись&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; расшифровка подписи", tiny)],
            [Paragraph("М.П.", base), Paragraph("Дата подписания (принятия) работ (услуг): ________________&nbsp;&nbsp;&nbsp; М.П.", base)],
        ],
        colWidths=[123.5 * mm, 123.5 * mm],
        hAlign="LEFT",
    )
    signatures.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#777777")),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(KeepTogether(signatures))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "* Применяется для приемки-передачи выполненных работ (оказанных услуг), "
            "за исключением строительно-монтажных работ.",
            tiny,
        )
    )

    def draw_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont(regular, 6)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawRightString(page_width - 12 * mm, 5 * mm, f"Страница {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=draw_page_number, onLaterPages=draw_page_number)
    return buffer.getvalue()
