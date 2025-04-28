from llama_cpp import Llama
import pandas as pd
import os

# Load the model (already installed earlier)
llm = Llama(
    model_path=r"C:\Users\garv\OneDrive\Desktop\UNITY\Data Science\Deep Learning\Finan\Downloads\mistral-7b-instruct-v0.1.Q4_K_M.gguf",  # Adjust path if needed
    n_ctx=1500,
    n_threads=8
)

# Load extracted document parts
with open(r"C:\Users\garv\OneDrive\Desktop\UNITY\Data Science\Deep Learning\Finan\PDF\fake_itr_perfect\itr_text.txt", "r", encoding="utf-8") as f:
    itr_text = f.read()

# Dynamically load all CSV files from the directory
csv_dir = r"C:\Users\garv\OneDrive\Desktop\UNITY\Data Science\Deep Learning\Finan\PDF\fake_itr_perfect"
csv_files = [file for file in os.listdir(csv_dir) if file.endswith(".csv")]

# Convert all tables to readable strings
tables_text = []
for csv_file in csv_files:
    table_path = os.path.join(csv_dir, csv_file)
    table_df = pd.read_csv(table_path)
    tables_text.append(f"--- {csv_file} ---\n{table_df.to_string(index=False)}")

# Combine all tables into a single string
all_tables_text = "\n\n".join(tables_text)

# Dynamic business context
print("\nPlease provide the business context (e.g., business type, turnover, goals, etc.):")
business_context = input("Business Context: ")

# 🎯 Function to answer a single question
def answer_user_question(user_question):
    qa_prompt = f"""
        You are a financial assistant AI. The following is the user's Income Tax Return (ITR-1) data, extracted tables, and business context.

        --- OCR Text ---
        {itr_text}

        --- Extracted Tables ---
        {all_tables_text}

        --- Business Context ---
        {business_context}

        --- User Question ---
        {user_question}

        Answer clearly, practically, and use ₹ for currency. Be concise but specific.
        """
    # Generate the answer
    response = llm(qa_prompt, max_tokens=500, stop=["</s>"])
    return response["choices"][0]["text"].strip()

# Multiple Question Loop
print("\n✅ Document loaded. You can now ask questions!")
print("Type 'exit' to quit.\n")

while True:
    user_question = input("Your Question: ")
    if user_question.lower() == "exit":
        break
    
    answer = answer_user_question(user_question)
    print("\n Answer:\n")
    print(answer)
    print("\n" + "="*60 + "\n")