"""
Synthetic Document Generator for DocuReady MVP
Generates realistic, completely synthetic PDF documents with verifiable visual text
and structural layout for all 6 required document types using ReportLab.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def _create_base_doc(pdf_path: str):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    return doc


def generate_income_certificate(
    pdf_path: str,
    applicant_name: str,
    father_name: str,
    annual_income: str,
    issue_date: str,
    certificate_no: str,
    state: str = "ODISHA",
    district: str = "KHORDHA",
    tahsil: str = "BHUBANESWAR",
    is_unreadable: bool = False
):
    """Generates synthetic Government Income Certificate PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = _create_base_doc(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    if is_unreadable:
        # Generates a smudged/unreadable document
        p_unreadable = Paragraph("<font size=14 color='#999999'>[ILLEGIBLE / CORRUPTED SCAN - OCR QUALITY 0.12]</font>", styles["Normal"])
        story.append(Spacer(1, 200))
        story.append(p_unreadable)
        story.append(Paragraph("<font size=9 color='#cccccc'>XXXXX ????? ###### ~~~~~</font>", styles["Normal"]))
        doc.build(story)
        return pdf_path

    # Title Banner
    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor('#1A365D')
    )
    sub_title = ParagraphStyle(
        'GovSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor('#4A5568')
    )

    story.append(Paragraph(f"GOVERNMENT OF {state.upper()}", title_style))
    story.append(Paragraph("REVENUE & DISASTER MANAGEMENT DEPARTMENT", sub_title))
    story.append(Paragraph(f"OFFICE OF THE TAHSILDAR, {tahsil.upper()}, {district.upper()}", sub_title))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A365D')))
    story.append(Spacer(1, 12))

    cert_banner = ParagraphStyle(
        'CertBanner',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        alignment=1,
        textColor=colors.HexColor('#2B6CB0')
    )
    story.append(Paragraph("INCOME CERTIFICATE", cert_banner))
    story.append(Spacer(1, 15))

    # Certificate Metadata Table
    meta_data = [
        [
            Paragraph(f"<b>Certificate No:</b> {certificate_no}", styles['Normal']),
            Paragraph(f"<b>Issue Date:</b> {issue_date}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Statutory Reference:</b> Odisha Misc Cert Rules 2019", styles['Normal']),
            Paragraph(f"<b>Valid For:</b> 3 Years from issue", styles['Normal'])
        ]
    ]
    t_meta = Table(meta_data, colWidths=[270, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 18))

    body_text = f"""
    This is to certify that <b>{applicant_name}</b>, Son/Daughter of <b>{father_name}</b>,
    resident of Tahsil {tahsil}, District {district}, in the State of {state},
    has a total verified annual family income from all sources of:
    """
    story.append(Paragraph(body_text, styles['Normal']))
    story.append(Spacer(1, 12))

    income_box = [
        [
            Paragraph("<font size=11><b>Annual Family Income (in figures):</b></font>", styles['Normal']),
            Paragraph(f"<font size=13 color='#1A365D'><b>{annual_income}</b></font>", styles['Normal'])
        ],
        [
            Paragraph("<font size=10><b>Income Assessment Year:</b></font>", styles['Normal']),
            Paragraph("<font size=10>2024-2025</font>", styles['Normal'])
        ]
    ]
    t_income = Table(income_box, colWidths=[260, 260])
    t_income.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3182CE')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF8FF')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_income)
    story.append(Spacer(1, 40))

    # Signatory
    sig_data = [
        ["", "Digitally Signed by:"],
        ["", f"Revenue Officer / Tahsildar, {tahsil}"],
        ["", f"Government of {state}"]
    ]
    t_sig = Table(sig_data, colWidths=[320, 200])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#4A5568')),
    ]))
    story.append(t_sig)

    doc.build(story)
    return pdf_path


def generate_caste_certificate(
    pdf_path: str,
    applicant_name: str,
    father_name: str,
    caste_category: str,
    sub_caste: str,
    issue_date: str,
    certificate_no: str,
    state: str = "ODISHA",
    district: str = "KHORDHA"
):
    """Generates synthetic Government Caste/Community Certificate PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = _create_base_doc(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor('#742A2A')
    )
    sub_title = ParagraphStyle(
        'GovSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor('#4A5568')
    )

    story.append(Paragraph(f"GOVERNMENT OF {state.upper()}", title_style))
    story.append(Paragraph("DEPARTMENT OF ST & SC DEVELOPMENT, MINORITIES & BACKWARD CLASSES", sub_title))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#742A2A')))
    story.append(Spacer(1, 10))

    cert_banner = ParagraphStyle(
        'CertBanner',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        alignment=1,
        textColor=colors.HexColor('#9B2C2C')
    )
    story.append(Paragraph("COMMUNITY / CASTE CERTIFICATE", cert_banner))
    story.append(Spacer(1, 15))

    meta_data = [
        [
            Paragraph(f"<b>Certificate No:</b> {certificate_no}", styles['Normal']),
            Paragraph(f"<b>Issue Date:</b> {issue_date}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Issuing Authority:</b> Sub-Divisional Magistrate", styles['Normal']),
            Paragraph(f"<b>District:</b> {district}", styles['Normal'])
        ]
    ]
    t_meta = Table(meta_data, colWidths=[270, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF5F5')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#FEB2B2')),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 18))

    body_text = f"""
    This is to certify that <b>{applicant_name}</b>, Son/Daughter of <b>{father_name}</b>,
    of District {district} in the State of {state}, belongs to the <b>{sub_caste}</b> community
    which is recognized as a <b>{caste_category}</b> under the Constitution (Scheduled Castes/Scheduled Tribes/OBC) Order.
    """
    story.append(Paragraph(body_text, styles['Normal']))
    story.append(Spacer(1, 15))

    caste_box = [
        [
            Paragraph("<b>Applicant Name:</b>", styles['Normal']),
            Paragraph(f"<b>{applicant_name}</b>", styles['Normal'])
        ],
        [
            Paragraph("<b>Recognized Category:</b>", styles['Normal']),
            Paragraph(f"<font color='#9B2C2C'><b>{caste_category}</b></font>", styles['Normal'])
        ],
        [
            Paragraph("<b>Sub-Caste / Tribe:</b>", styles['Normal']),
            Paragraph(f"<b>{sub_caste}</b>", styles['Normal'])
        ]
    ]
    t_caste = Table(caste_box, colWidths=[200, 320])
    t_caste.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E53E3E')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF5F5')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FEB2B2'))
    ]))
    story.append(t_caste)
    story.append(Spacer(1, 40))

    sig_data = [
        ["", "Signed and Sealed by:"],
        ["", f"Sub-Collector / SDM, {district}"],
        ["", f"Government of {state}"]
    ]
    t_sig = Table(sig_data, colWidths=[320, 200])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#4A5568')),
    ]))
    story.append(t_sig)

    doc.build(story)
    return pdf_path


def generate_residence_certificate(
    pdf_path: str,
    applicant_name: str,
    father_name: str,
    address: str,
    state: str = "ODISHA",
    district: str = "KHORDHA",
    issue_date: str = "15/01/2025",
    certificate_no: str = "RES/2025/99812"
):
    """Generates synthetic Resident/Domicile Certificate PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = _create_base_doc(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor('#22543D')
    )
    sub_title = ParagraphStyle(
        'GovSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor('#4A5568')
    )

    story.append(Paragraph(f"GOVERNMENT OF {state.upper()}", title_style))
    story.append(Paragraph("DEPARTMENT OF REVENUE & LAND RECORDS", sub_title))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#22543D')))
    story.append(Spacer(1, 10))

    cert_banner = ParagraphStyle(
        'CertBanner',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        alignment=1,
        textColor=colors.HexColor('#276749')
    )
    story.append(Paragraph("RESIDENT / DOMICILE CERTIFICATE", cert_banner))
    story.append(Spacer(1, 15))

    meta_data = [
        [
            Paragraph(f"<b>Certificate No:</b> {certificate_no}", styles['Normal']),
            Paragraph(f"<b>Issue Date:</b> {issue_date}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Territorial Jurisdiction:</b> {district}", styles['Normal']),
            Paragraph(f"<b>State:</b> {state}", styles['Normal'])
        ]
    ]
    t_meta = Table(meta_data, colWidths=[270, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FFF4')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#9AE6B4')),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 18))

    body_text = f"""
    This is to certify that <b>{applicant_name}</b>, Son/Daughter of <b>{father_name}</b>,
    is a bonafide permanent resident of <b>{address}</b>, District {district}, in the State of <b>{state}</b>.
    This certificate is issued for educational, scholarship and statutory purposes.
    """
    story.append(Paragraph(body_text, styles['Normal']))
    story.append(Spacer(1, 15))

    info_box = [
        [
            Paragraph("<b>Applicant Full Name:</b>", styles['Normal']),
            Paragraph(f"<b>{applicant_name}</b>", styles['Normal'])
        ],
        [
            Paragraph("<b>Father's / Guardian's Name:</b>", styles['Normal']),
            Paragraph(f"<b>{father_name}</b>", styles['Normal'])
        ],
        [
            Paragraph("<b>Domicile State:</b>", styles['Normal']),
            Paragraph(f"<font color='#22543D'><b>{state.upper()}</b></font>", styles['Normal'])
        ]
    ]
    t_info = Table(info_box, colWidths=[200, 320])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#38A169')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FFF4')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#9AE6B4'))
    ]))
    story.append(t_info)
    story.append(Spacer(1, 40))

    sig_data = [
        ["", "Digitally Signed by:"],
        ["", f"Additional Tahsildar / Executive Magistrate"],
        ["", f"Government of {state}"]
    ]
    t_sig = Table(sig_data, colWidths=[320, 200])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#4A5568')),
    ]))
    story.append(t_sig)

    doc.build(story)
    return pdf_path


def generate_marksheet(
    pdf_path: str,
    applicant_name: str,
    father_name: str,
    dob: str,
    roll_no: str,
    percentage: float,
    exam_name: str = "Class 10 High School Certificate Examination",
    board_name: str = "BOARD OF SECONDARY EDUCATION, ODISHA",
    passing_year: str = "2024"
):
    """Generates synthetic Academic Marksheet PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = _create_base_doc(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'BoardTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,
        textColor=colors.HexColor('#2D3748')
    )
    sub_title = ParagraphStyle(
        'BoardSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        alignment=1,
        textColor=colors.HexColor('#4A5568')
    )

    story.append(Paragraph(board_name, title_style))
    story.append(Paragraph(f"MARKS STATEMENT — {exam_name.upper()} ({passing_year})", sub_title))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2D3748')))
    story.append(Spacer(1, 10))

    # Candidate Profile Table
    cand_data = [
        [
            Paragraph(f"<b>Candidate Name:</b> {applicant_name}", styles['Normal']),
            Paragraph(f"<b>Roll No:</b> {roll_no}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Father's Name:</b> {father_name}", styles['Normal']),
            Paragraph(f"<b>Date of Birth:</b> {dob}", styles['Normal'])
        ]
    ]
    t_cand = Table(cand_data, colWidths=[280, 240])
    t_cand.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_cand)
    story.append(Spacer(1, 14))

    # Subject Marks Breakdown
    # Compute proportional marks based on total percentage
    tot_marks = int(percentage * 6)
    marks_table_data = [
        ["Sub Code", "Subject Name", "Max Marks", "Marks Obtained"],
        ["01", "FIRST LANGUAGE (FLO)", "100", str(int(percentage + 2))],
        ["02", "SECOND LANGUAGE (SLE)", "100", str(int(percentage - 1))],
        ["03", "THIRD LANGUAGE (TLS)", "100", str(int(percentage + 1))],
        ["04", "MATHEMATICS (MTH)", "100", str(int(percentage))],
        ["05", "SCIENCE (GSC)", "100", str(int(percentage - 2))],
        ["06", "SOCIAL SCIENCE (SSC)", "100", str(int(percentage))],
        ["TOTAL", "AGGREGATE RESULT", "600", f"{tot_marks} ({percentage:.1f}%)"]
    ]
    t_marks = Table(marks_table_data, colWidths=[80, 220, 100, 120])
    t_marks.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EBF8FF')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_marks)
    story.append(Spacer(1, 35))

    sig_data = [
        ["Date of Result: 26/05/2024", "Controller of Examinations"]
    ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#4A5568')),
    ]))
    story.append(t_sig)

    doc.build(story)
    return pdf_path


def generate_bank_passbook(
    pdf_path: str,
    applicant_name: str,
    account_no: str,
    ifsc: str,
    bank_name: str = "State Bank of India",
    branch: str = "Bhubaneswar Main Branch",
    dbt_status: str = "NPCI Aadhaar Mapped / DBT Active"
):
    """Generates synthetic Bank Passbook front-page scan PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = _create_base_doc(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'BankTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor('#2C5282')
    )
    sub_title = ParagraphStyle(
        'BankSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor('#4A5568')
    )

    story.append(Paragraph(bank_name.upper(), title_style))
    story.append(Paragraph(f"SAVINGS BANK PASSBOOK — {branch.upper()}", sub_title))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2C5282')))
    story.append(Spacer(1, 14))

    passbook_data = [
        [
            Paragraph("<b>Account Holder Name:</b>", styles['Normal']),
            Paragraph(f"<b>{applicant_name}</b>", styles['Normal'])
        ],
        [
            Paragraph("<b>Account Number:</b>", styles['Normal']),
            Paragraph(f"<b>{account_no}</b>", styles['Normal'])
        ],
        [
            Paragraph("<b>Bank IFSC Code:</b>", styles['Normal']),
            Paragraph(f"<b>{ifsc}</b>", styles['Normal'])
        ],
        [
            Paragraph("<b>Branch Name:</b>", styles['Normal']),
            Paragraph(branch, styles['Normal'])
        ],
        [
            Paragraph("<b>DBT / Aadhaar Seeding:</b>", styles['Normal']),
            Paragraph(f"<font color='#276749'><b>{dbt_status}</b></font>", styles['Normal'])
        ]
    ]
    t_pass = Table(passbook_data, colWidths=[200, 320])
    t_pass.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#2B6CB0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF8FF')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BEE3F8')),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_pass)
    story.append(Spacer(1, 40))

    sig_data = [
        ["Authorized Signatory / Branch Manager", "Official Branch Round Seal"]
    ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#718096')),
    ]))
    story.append(t_sig)

    doc.build(story)
    return pdf_path


def generate_application_form(
    pdf_path: str,
    applicant_name: str,
    father_name: str,
    dob: str,
    annual_income: str,
    caste_category: str,
    scheme_name: str = "Post-Matric Scholarship (SC/ST/OBC)",
    income_cert_no: str = "E-INC/2025/104928",
    caste_cert_no: str = "CST/2025/88192",
    residence_cert_no: str = "RES/2025/99812",
    account_no: str = "30987654301",
    ifsc: str = "SBIN0001234"
):
    """Generates synthetic Scheme Online Application Form PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = _create_base_doc(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'AppTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,
        textColor=colors.HexColor('#1A202C')
    )
    sub_title = ParagraphStyle(
        'AppSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor('#2B6CB0')
    )

    story.append(Paragraph("COMMON SCHOLARSHIP PORTAL", title_style))
    story.append(Paragraph(f"APPLICATION ACKNOWLEDGEMENT RECEIPT — {scheme_name.upper()}", sub_title))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A202C')))
    story.append(Spacer(1, 10))

    # Form Fields Table
    form_fields = [
        ["Section 1: Applicant Demographics", ""],
        ["Applicant Full Name:", applicant_name],
        ["Father's / Guardian's Name:", father_name],
        ["Date of Birth (DOB):", dob],
        ["Social Category:", caste_category],
        ["Declared Annual Family Income:", annual_income],
        ["Section 2: Enclosed Certificate Details", ""],
        ["Income Certificate Reference No:", income_cert_no],
        ["Caste Certificate Reference No:", caste_cert_no],
        ["Residence Certificate Reference No:", residence_cert_no],
        ["Section 3: Bank Details for DBT", ""],
        ["Bank Account Number:", account_no],
        ["Bank IFSC Code:", ifsc]
    ]

    table_data = []
    for row in form_fields:
        if row[1] == "":
            table_data.append([
                Paragraph(f"<b>{row[0]}</b>", styles['Normal']),
                ""
            ])
        else:
            table_data.append([
                Paragraph(f"<b>{row[0]}</b>", styles['Normal']),
                Paragraph(row[1], styles['Normal'])
            ])

    t_form = Table(table_data, colWidths=[240, 280])
    t_form.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor('#EDF2F7')),
        ('BACKGROUND', (0,10), (-1,10), colors.HexColor('#EDF2F7')),
        ('SPAN', (0,0), (1,0)),
        ('SPAN', (0,6), (1,6)),
        ('SPAN', (0,10), (1,10)),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_form)
    story.append(Spacer(1, 20))

    dec_text = (
        "<b>Applicant Declaration:</b> I hereby declare that the particulars stated above are true to the best of "
        "my knowledge and that the uploaded certificates have been verified from official revenue records."
    )
    story.append(Paragraph(dec_text, styles['Normal']))

    doc.build(story)
    return pdf_path
