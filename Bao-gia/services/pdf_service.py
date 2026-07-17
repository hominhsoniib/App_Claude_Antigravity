import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# --- Đăng ký font Unicode hỗ trợ dấu tiếng Việt (Helvetica mặc định KHÔNG hỗ trợ) ---
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
_DEJAVU_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Fallback cho Windows
_WIN_ARIAL_REGULAR = r"C:\Windows\Fonts\arial.ttf"
_WIN_ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

if os.path.exists(_DEJAVU_REGULAR) and os.path.exists(_DEJAVU_BOLD):
    pdfmetrics.registerFont(TTFont("DejaVuSans", _DEJAVU_REGULAR))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _DEJAVU_BOLD))
    pdfmetrics.registerFontFamily(
        "DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold",
        italic="DejaVuSans", boldItalic="DejaVuSans-Bold",
    )
    FONT_REGULAR = "DejaVuSans"
    FONT_BOLD = "DejaVuSans-Bold"
elif os.path.exists(_WIN_ARIAL_REGULAR) and os.path.exists(_WIN_ARIAL_BOLD):
    pdfmetrics.registerFont(TTFont("Arial", _WIN_ARIAL_REGULAR))
    pdfmetrics.registerFont(TTFont("Arial-Bold", _WIN_ARIAL_BOLD))
    pdfmetrics.registerFontFamily(
        "Arial", normal="Arial", bold="Arial-Bold",
        italic="Arial", boldItalic="Arial-Bold",
    )
    FONT_REGULAR = "Arial"
    FONT_BOLD = "Arial-Bold"

COMPANY_NAME = "CÔNG TY TNHH GIẢI PHÁP CÔNG NGHIỆP VIỆT"
COMPANY_ADDR = "123 Đường Công Nghiệp, Q. Bình Tân, TP.HCM"
COMPANY_TAX = "0312345678"
COMPANY_PHONE = "(028) 3838 3838   |   Email: sales@congty.vn"


def generate_quote_pdf(header):
    """Sinh file PDF báo giá từ QuotationHeader (đã load kèm details/customer)."""
    file_path = os.path.join(EXPORT_DIR, f"{header.quote_no}.pdf")
    doc = SimpleDocTemplate(file_path, pagesize=A4,
                             topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=15 * mm, rightMargin=15 * mm)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("normalVN", parent=styles["Normal"], fontName=FONT_REGULAR)
    title_style = ParagraphStyle("TitleVN", parent=normal,
                                  fontName=FONT_BOLD, fontSize=18, alignment=1, spaceAfter=4)
    small = ParagraphStyle("small", parent=normal, fontSize=9, leading=12)
    header_style = ParagraphStyle("hdr", parent=normal, fontName=FONT_BOLD, fontSize=10, leading=14)

    elems = []
    elems.append(Paragraph(f"<b>{COMPANY_NAME}</b>", header_style))
    elems.append(Paragraph(COMPANY_ADDR, small))
    elems.append(Paragraph(f"MST: {COMPANY_TAX} &nbsp;&nbsp; {COMPANY_PHONE}", small))
    elems.append(Spacer(1, 10))
    elems.append(Paragraph("BÁO GIÁ", title_style))
    elems.append(Paragraph(f"Số: <b>{header.quote_no}</b>", ParagraphStyle(
        "quoteno", parent=normal, alignment=1, fontSize=11)))
    elems.append(Spacer(1, 10))

    cust = header.customer
    info_data = [
        ["Khách hàng:", cust.name if cust else "", "Ngày báo giá:", header.quote_date.strftime("%d/%m/%Y")],
        ["Địa chỉ:", (cust.address if cust else "") or "", "Hiệu lực đến:", header.valid_until.strftime("%d/%m/%Y") if header.valid_until else ""],
        ["Mã số thuế:", (cust.tax_code if cust else "") or "", "Điều kiện TT:", header.payment_terms or ""],
        ["Điều kiện giao hàng:", header.delivery_terms or "", "Thời gian giao:", header.lead_time or ""],
    ]
    info_table = Table(info_data, colWidths=[38 * mm, 62 * mm, 32 * mm, 48 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
        ("FONTNAME", (2, 0), (2, -1), FONT_BOLD),
    ]))
    elems.append(info_table)
    elems.append(Spacer(1, 12))

    # Bảng chi tiết
    data = [["STT", "Sản phẩm", "ĐVT", "SL", "Đơn giá", "CK%", "VAT%", "Thành tiền"]]
    for i, d in enumerate(header.details, start=1):
        data.append([
            str(i),
            d.product.name if d.product else "",
            d.product.unit if d.product else "",
            f"{d.qty:g}",
            f"{d.unit_price:,.0f}",
            f"{d.discount_pct:g}%",
            f"{d.vat_pct:g}%",
            f"{d.line_total:,.0f}",
        ])
    table = Table(data, colWidths=[10*mm, 55*mm, 15*mm, 15*mm, 25*mm, 13*mm, 13*mm, 30*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ]))
    elems.append(table)
    elems.append(Spacer(1, 8))

    totals_data = [
        ["Tạm tính:", f"{header.subtotal:,.0f} đ"],
        ["VAT:", f"{header.vat_total:,.0f} đ"],
        ["Phí vận chuyển:", f"{header.shipping_fee:,.0f} đ"],
        ["Chi phí khác:", f"{header.other_fee:,.0f} đ"],
        ["TỔNG CỘNG:", f"{header.grand_total:,.0f} đ"],
    ]
    totals_table = Table(totals_data, colWidths=[130 * mm, 46 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
    ]))
    elems.append(totals_table)
    elems.append(Spacer(1, 14))

    if header.note:
        elems.append(Paragraph(f"<b>Ghi chú:</b> {header.note}", small))
        elems.append(Spacer(1, 10))

    terms = (
        "Điều khoản: Báo giá có hiệu lực trong thời gian nêu trên. "
        "Giá trên chưa bao gồm các chi phí phát sinh ngoài phạm vi báo giá (nếu có). "
        "Bảo hành theo chính sách của nhà sản xuất."
    )
    elems.append(Paragraph(terms, small))
    elems.append(Spacer(1, 20))

    from models.models import QuoteStatus
    from services.stamp_service import get_stamp_and_signature_path

    # Tạo cụm chữ ký bên bán (có đóng dấu nếu đã duyệt)
    seller_flowables = [
        Paragraph("<b>Đại diện Bên Bán</b>", ParagraphStyle("slrHdr", parent=normal, fontName=FONT_BOLD, fontSize=10, alignment=1)),
        Spacer(1, 2)
    ]
    if header.status in (QuoteStatus.APPROVED, QuoteStatus.SENT, QuoteStatus.WON):
        stamp_img_path = get_stamp_and_signature_path(header.quote_date.strftime("%d/%m/%Y"))
        seller_flowables.append(Image(stamp_img_path, width=32*mm, height=32*mm, hAlign="CENTER"))
    else:
        seller_flowables.append(Spacer(1, 25))
        seller_flowables.append(Paragraph("(Ký, ghi rõ họ tên)", ParagraphStyle("slrSub", parent=normal, fontSize=9, alignment=1)))

    # Tạo cụm chữ ký bên mua
    buyer_flowables = [
        Paragraph("<b>Đại diện Bên Mua</b>", ParagraphStyle("byrHdr", parent=normal, fontName=FONT_BOLD, fontSize=10, alignment=1)),
        Spacer(1, 25),
        Paragraph("(Ký, ghi rõ họ tên)", ParagraphStyle("byrSub", parent=normal, fontSize=9, alignment=1))
    ]

    sign_data = [[seller_flowables, buyer_flowables]]
    sign_table = Table(sign_data, colWidths=[88 * mm, 88 * mm])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elems.append(sign_table)

    doc.build(elems)
    return file_path
