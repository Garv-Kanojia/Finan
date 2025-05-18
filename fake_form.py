from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from faker import Faker
from io import BytesIO
from PIL import Image as PILImage
import qrcode
import random
from reportlab.lib.utils import ImageReader


fake = Faker('en_IN')
styles = getSampleStyleSheet()

# --- HELPER FUNCTIONS ---
def generate_qr_image(text):
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def add_heading(canvas_obj, text, x, y, font="Helvetica-Bold", size=12):
    canvas_obj.setFont(font, size)
    canvas_obj.drawString(x, y, text)
    return y - 20

def add_table(canvas_obj, data, x, y, col_widths, style=None):
    table = Table(data, colWidths=col_widths)
    if style:
        table.setStyle(style)
    table.wrapOn(canvas_obj, 0, 0)
    table.drawOn(canvas_obj, x, y - table._height)
    return y - table._height - 15

# --- MAIN FUNCTION ---
def generate_realistic_itr_buffer():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # ===== PAGE 1: COVER PAGE =====
    y = height - 50
    y = add_heading(c, "INCOME TAX RETURN - SAHAJ (ITR-1)", width / 2 - 100, y, size=14)
    y = add_heading(c, "Assessment Year: 2024-25 | Form Applicable for AY 2024-25", width / 2 - 150, y, size=10)

    pan = "AAAAA" + str(random.randint(1000, 9999)) + "A"
    personal_data = [
        ["Name", fake.name(), "PAN", pan],
        ["Date of Birth", fake.date(pattern="%d/%m/%Y"), "Gender", random.choice(["Male", "Female"])],
        ["Aadhaar", fake.unique.numerify("##########"), "Mobile", fake.phone_number()],
        ["Address", fake.address().replace("\n", ", ")[:100], "", ""]
    ]
    y = add_table(c, personal_data, 50, y - 30, [80, 150, 80, 150],
                  TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                              ('FONTSIZE', (0, 0), (-1, -1), 9)]))

    qr_image = generate_qr_image(f"ITR1|{pan}|2024-25|{random.randint(100000,999999)}")
    c.drawImage(ImageReader(qr_image), width - 120, y - 100, width=80, height=80, mask='auto')
    c.showPage()

    # ===== PAGE 2: INCOME DETAILS =====
    y = height - 50
    y = add_heading(c, "Part B: Gross Total Income", 50, y)

    salary_data = [
        ["Particulars", "Amount (₹)"],
        ["Basic Salary", f"{random.randint(400000, 800000):,}"],
        ["House Rent Allowance", f"{random.randint(50000, 200000):,}"],
        ["Special Allowances", f"{random.randint(30000, 100000):,}"],
        ["Total Salary Income", f"{random.randint(500000, 900000):,}"]
    ]
    y = add_table(c, salary_data, 50, y - 20, [300, 100],
                  TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                              ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))

    y = add_heading(c, "Other Income Sources", 50, y - 30)
    other_income_data = [
        ["Source", "Amount (₹)"],
        ["Interest from Savings Account", f"{random.randint(5000, 30000):,}"],
        ["Fixed Deposits Interest", f"{random.randint(10000, 50000):,}"],
        ["Dividend Income", f"{random.randint(2000, 15000):,}"]
    ]
    y = add_table(c, other_income_data, 50, y - 20, [300, 100],
                  TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                              ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
    c.showPage()

    # ===== PAGE 3: DEDUCTIONS =====
    y = height - 50
    y = add_heading(c, "Part C: Deductions (Chapter VI-A)", 50, y)

    deduction_data = [
        ["Section", "Particulars", "Amount (₹)"],
        ["80C", "Life Insurance Premium", f"{random.randint(10000, 150000):,}"],
        ["80D", "Health Insurance", f"{random.randint(10000, 50000):,}"],
        ["80G", "Donations", f"{random.randint(5000, 30000):,}"],
        ["80TTA", "Interest Income", f"{random.randint(2000, 10000):,}"]
    ]
    y = add_table(c, deduction_data, 50, y - 20, [50, 200, 100],
                  TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                              ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))

    # Tax Computation
    y = add_heading(c, "Part D: Tax Computation", 50, y - 40)
    taxable_income = random.randint(500000, 1000000)
    tax_data = [
        ["Particulars", "Amount (₹)"],
        ["Gross Total Income", f"{taxable_income + 150000:,}"],
        ["Total Deductions", "1,50,000"],
        ["Taxable Income", f"{taxable_income:,}"],
        ["Tax on Total Income", f"{int(taxable_income * 0.1):,}"],
        ["Rebate (87A)", "12,500"],
        ["Total Tax Payable", f"{max(0, int(taxable_income * 0.1) - 12500):,}"],
        ["TDS/Advance Tax", f"{random.randint(10000, 50000):,}"],
        ["Balance Tax Payable", f"{max(0, int(taxable_income * 0.1) - 12500 - random.randint(10000, 50000)):,}"]
    ]
    y = add_table(c, tax_data, 50, y - 20, [300, 100],
                  TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                              ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                              ('ALIGN', (1, 0), (1, -1), 'RIGHT')]))
    c.showPage()

    # ===== PAGE 4: VERIFICATION =====
    y = height - 50
    y = add_heading(c, "Part E: Verification", 50, y)

    verification_text = f"""
    I, <b>{fake.name()}</b>, solemnly declare that:<br/>
    1. The information given in this return is correct and complete.<br/>
    2. I am filing this return in my capacity as <b>Individual</b>.<br/>
    3. No search/survey has been conducted under section 132/133A.<br/><br/>
    Place: {fake.city()}<br/>
    Date: {fake.date(pattern='%d/%m/%Y')}<br/><br/>
    <b>Digital Signature:</b> _______________________
    """
    verification_para = Paragraph(verification_text, styles['Normal'])
    verification_para.wrapOn(c, width - 100, height)
    verification_para.drawOn(c, 50, y - 100)

    # Bank Details
    y = add_heading(c, "Bank Account Details for Refund", 50, y - 150)
    bank_data = [
        ["Bank Name", random.choice(["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank"])],
        ["Account Number", fake.bban()],
        ["IFSC Code", "YESB" + fake.numerify("0#########")],
        ["Account Type", random.choice(["Savings", "Current"])]
    ]
    add_table(c, bank_data, 50, y - 20, [100, 200],
              TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))

    c.save()
    buffer.seek(0)
    return buffer

def generate_realistic_itr(pdf_buffer=None):
    buffer = generate_realistic_itr_buffer()
    if pdf_buffer is not None:
        pdf_buffer.write(buffer.read())
        pdf_buffer.seek(0)
    else:
        return buffer