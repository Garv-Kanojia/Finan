from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from faker import Faker
import qrcode
import io
import random
import tempfile
import os

fake = Faker('en_IN')
styles = getSampleStyleSheet()

# --- HELPER FUNCTIONS ---
def generate_qr(text):
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_dir = tempfile.gettempdir()
    qr_path = os.path.join(temp_dir, "temp_qr.png")
    img.save(qr_path)
    return qr_path

def add_heading(canvas, text, x, y, font="Helvetica-Bold", size=12):
    canvas.setFont(font, size)
    canvas.drawString(x, y, text)
    return y - 20  # Return new Y position after heading

def add_table(canvas, data, x, y, col_widths, style=None):
    table = Table(data, colWidths=col_widths)
    if style:
        table.setStyle(style)
    table.wrapOn(canvas, 0, 0)
    table.drawOn(canvas, x, y - table._height)
    return y - table._height - 15  # Return new Y position after table

# --- MAIN FUNCTION ---
def generate_realistic_itr(output_path="fake_itr_perfect.pdf"):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # ===== PAGE 1: COVER PAGE =====
    y_position = height - 50
    y_position = add_heading(c, "INCOME TAX RETURN - SAHAJ (ITR-1)", width/2-100, y_position, "Helvetica-Bold", 14)
    y_position = add_heading(c, "Assessment Year: 2024-25 | Form Applicable for AY 2024-25", width/2-150, y_position, "Helvetica", 10)
    
    # Personal Details Table
    pan = "AAAAA" + str(random.randint(1000,9999)) + "A"
    personal_data = [
        ["Name", fake.name(), "PAN", pan],
        ["Date of Birth", fake.date(pattern="%d/%m/%Y"), "Gender", random.choice(["Male", "Female"])],
        ["Aadhaar", fake.unique.numerify("##########"), "Mobile", fake.phone_number()],
        ["Address", fake.address().replace("\n", ", ")[:100], "", ""]
    ]
    y_position = add_table(c, personal_data, 50, y_position - 30, [80, 150, 80, 150], 
                         TableStyle([('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                                   ('FONTSIZE', (0,0), (-1,-1), 9)]))

    # QR Code
    qr_path = generate_qr(f"ITR1|{pan}|2024-25|{random.randint(100000,999999)}")
    c.drawImage(qr_path, width-120, y_position - 100, width=80, height=80)
    os.remove(qr_path)
    c.showPage()

    # ===== PAGE 2: INCOME DETAILS =====
    y_position = height - 50
    y_position = add_heading(c, "Part B: Gross Total Income", 50, y_position)
    
    # Salary Table
    salary_data = [
        ["Particulars", "Amount (₹)"],
        ["Basic Salary", f"{random.randint(400000,800000):,}"],
        ["House Rent Allowance", f"{random.randint(50000,200000):,}"],
        ["Special Allowances", f"{random.randint(30000,100000):,}"],
        ["Total Salary Income", f"{random.randint(500000,900000):,}"]
    ]
    y_position = add_table(c, salary_data, 50, y_position - 20, [300, 100],
                          TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                                    ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))

    # Other Income Heading
    y_position = add_heading(c, "Other Income Sources", 50, y_position - 30)
    
    # Other Income Table
    other_income_data = [
        ["Source", "Amount (₹)"],
        ["Interest from Savings Account", f"{random.randint(5000,30000):,}"],
        ["Fixed Deposits Interest", f"{random.randint(10000,50000):,}"],
        ["Dividend Income", f"{random.randint(2000,15000):,}"]
    ]
    y_position = add_table(c, other_income_data, 50, y_position - 20, [300, 100],
                         TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                                   ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    c.showPage()

    # ===== PAGE 3: DEDUCTIONS & TAX =====
    y_position = height - 50
    y_position = add_heading(c, "Part C: Deductions (Chapter VI-A)", 50, y_position)
    
    # Deductions Table
    deduction_data = [
        ["Section", "Particulars", "Amount (₹)"],
        ["80C", "Life Insurance Premium", f"{random.randint(10000,150000):,}"],
        ["80D", "Health Insurance", f"{random.randint(10000,50000):,}"],
        ["80G", "Donations", f"{random.randint(5000,30000):,}"],
        ["80TTA", "Interest Income", f"{random.randint(2000,10000):,}"]
    ]
    y_position = add_table(c, deduction_data, 50, y_position - 20, [50, 200, 100],
                         TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                                   ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))

    # Tax Computation Heading
    y_position = add_heading(c, "Part D: Tax Computation", 50, y_position - 40)
    
    # Tax Table
    taxable_income = random.randint(500000, 1000000)
    tax_data = [
        ["Particulars", "Amount (₹)"],
        ["Gross Total Income", f"{taxable_income + 150000:,}"],
        ["Total Deductions", "1,50,000"],
        ["Taxable Income", f"{taxable_income:,}"],
        ["Tax on Total Income", f"{int(taxable_income*0.1):,}"],
        ["Rebate (87A)", "12,500"],
        ["Total Tax Payable", f"{max(0, int(taxable_income*0.1)-12500):,}"],
        ["TDS/Advance Tax", f"{random.randint(10000,50000):,}"],
        ["Balance Tax Payable", f"{max(0, int(taxable_income*0.1)-12500-random.randint(10000,50000)):,}"]
    ]
    y_position = add_table(c, tax_data, 50, y_position - 20, [300, 100],
                         TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                                   ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                                   ('ALIGN', (1,0), (1,-1), 'RIGHT')]))
    c.showPage()

    # ===== PAGE 4: VERIFICATION =====
    y_position = height - 50
    y_position = add_heading(c, "Part E: Verification", 50, y_position)
    
    # Verification Text
    verification_text = f"""
    I, <b>{fake.name()}</b>, solemnly declare that:<br/>
    1. The information given in this return is correct and complete.<br/>
    2. I am filing this return in my capacity as <b>Individual</b>.<br/>
    3. No search/survey has been conducted under section 132/133A.<br/><br/>
    Place: {fake.city()}<br/>
    Date: {fake.date(pattern='%d/%m/%Y')}<br/><br/>
    <b>Digital Signature:</b> _______________________
    """
    verification = Paragraph(verification_text, styles['Normal'])
    verification.wrapOn(c, width-100, height)
    verification.drawOn(c, 50, y_position - 100)

    # Bank Details Heading
    y_position = add_heading(c, "Bank Account Details for Refund", 50, y_position - 150)
    
    # Bank Table
    bank_data = [
        ["Bank Name", random.choice(["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank"])],
        ["Account Number", fake.bban()],
        ["IFSC Code", "YESB" + fake.numerify("0#########")],
        ["Account Type", random.choice(["Savings", "Current"])]
    ]
    add_table(c, bank_data, 50, y_position - 20, [100, 200],
             TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))

    c.save()
    print(f"Perfectly formatted ITR generated: {output_path}")

generate_realistic_itr()