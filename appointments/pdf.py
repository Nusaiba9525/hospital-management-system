from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_prescription_pdf(appointment):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.HexColor('#0d9488'))
    elements = []

    elements.append(Paragraph('MedCare Hospital', title_style))
    elements.append(Paragraph('Prescription', styles['Heading2']))
    elements.append(Spacer(1, 0.25 * inch))

    patient = appointment.patient
    doctor = appointment.doctor
    data = [
        ['Patient', patient.get_full_name() or patient.username],
        ['Doctor', f'Dr. {doctor.full_name}'],
        ['Department', str(doctor.department or 'General')],
        ['Date', appointment.date.strftime('%B %d, %Y')],
        ['Time', appointment.time.strftime('%I:%M %p')],
    ]
    table = Table(data, colWidths=[1.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph('<b>Prescription</b>', styles['Heading3']))
    prescription_text = appointment.prescription or 'No prescription recorded.'
    for line in prescription_text.split('\n'):
        elements.append(Paragraph(line or '&nbsp;', styles['Normal']))
        elements.append(Spacer(1, 0.05 * inch))

    if appointment.notes:
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph('<b>Doctor Notes</b>', styles['Heading3']))
        elements.append(Paragraph(appointment.notes, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
