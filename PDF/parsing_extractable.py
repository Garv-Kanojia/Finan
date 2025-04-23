import pdfplumber
import pandas as pd
import re
import os

# === Load the ITR PDF ===
pdf_path = r"C:\Users\garv\OneDrive\Desktop\UNITY\Data Science\Deep Learning\Finan\Downloads\fake_itr_perfect.pdf"  # Update path if needed
text_data = ""
tables_data = []
file = pdf_path.split("\\")[-1].split(".")[0]  # Extract file name without extension
output_dir = f"PDF\\{file}"
if not os.path.exists(file):
    os.makedirs(output_dir, exist_ok=True)

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\nProcessing page {i+1}...")
        
        # --- Extract plain text ---
        page_text = page.extract_text()
        if page_text:
            text_data += page_text + "\n"

        # --- Extract tables ---
        page_tables = page.extract_tables()
        for table in page_tables:
            df = pd.DataFrame(table[1:], columns=table[0])  # Convert to DataFrame
            tables_data.append(df)

# === Save plain text ===
with open(f"{output_dir}\\itr_text.txt", "w", encoding="utf-8") as f:
    f.write(text_data)

# === Optional: Extract PAN, Name, etc. using regex ===
def extract_pan(text):
    match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text)
    return match.group(1) if match else None

def extract_name(text):
    match = re.search(r"Name\s*:\s*([A-Za-z\s]+)", text)
    return match.group(1).strip() if match else None

pan = extract_pan(text_data)
name = extract_name(text_data)

print("\n🧾 Extracted Info:")
print("PAN:", pan)
print("Name:", name)

# === Save tables to CSVs ===
for i, table_df in enumerate(tables_data):
    table_df.to_csv(f"{output_dir}\\table_{i+1}.csv", index=False)
    print(f"Saved table_{i+1}.csv")