import csv
import io
from pathlib import Path

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def csv_response(invitation, report):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="assessment-{invitation.public_id}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(("Компетенция", "Процент", "Уровень", "Интерпретация", "Рекомендация"))
    for row in report["rows"]:
        writer.writerow((row.label, row.percentage, row.level_label, row.interpretation, row.recommendation))
    return response


def xlsx_response(invitation, report):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Результаты"
    sheet.append(("Респондент", invitation.email))
    sheet.append(("Дата", invitation.completed_at.strftime("%d.%m.%Y %H:%M") if invitation.completed_at else ""))
    sheet.append(())
    sheet.append(("Компетенция", "Процент", "Уровень", "Интерпретация", "Рекомендация"))
    for row in report["rows"]:
        sheet.append((row.label, row.percentage, row.level_label, row.interpretation, row.recommendation))
    for width, column in zip((30, 12, 18, 75, 75), "ABCDE"):
        sheet.column_dimensions[column].width = width
    stream = io.BytesIO()
    workbook.save(stream)
    response = HttpResponse(stream.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="assessment-{invitation.public_id}.xlsx"'
    return response


def _font_name():
    candidates = (Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("ReportFont", str(candidate)))
            return "ReportFont"
    return "Helvetica"


def pdf_response(invitation, report):
    stream = io.BytesIO()
    font = _font_name()
    document = SimpleDocTemplate(stream, pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = font
    story = [Paragraph("Результаты оценки", styles["Title"]), Spacer(1, 5*mm),
             Paragraph(f"Респондент: {invitation.email}", styles["BodyText"]),
             Paragraph(f"Дата: {invitation.completed_at.strftime('%d.%m.%Y %H:%M')}", styles["BodyText"]), Spacer(1, 5*mm)]
    data = [["Компетенция", "%", "Уровень"]] + [[row.label, str(row.percentage), row.level_label] for row in report["rows"]]
    table = Table(data, colWidths=(105*mm, 20*mm, 40*mm), repeatRows=1)
    table.setStyle(TableStyle([("FONTNAME", (0,0), (-1,-1), font), ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#203a67")),
                               ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .5, colors.HexColor("#d9d9d9")),
                               ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("PADDING", (0,0), (-1,-1), 6)]))
    story.extend((table, Spacer(1, 6*mm)))
    for row in report["rows"]:
        story.extend((Paragraph(f"{row.label} — {row.percentage}%", styles["Heading2"]),
                      Paragraph(row.interpretation, styles["BodyText"]), Paragraph(f"Рекомендация: {row.recommendation}", styles["BodyText"]), Spacer(1, 3*mm)))
    document.build(story)
    response = HttpResponse(stream.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="assessment-{invitation.public_id}.pdf"'
    return response
