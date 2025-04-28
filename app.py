import streamlit as st
import pdfplumber
import pandas as pd
import os
import shutil
import re
from llama_cpp import Llama

# --- Model Loading ---
@st.cache_resource
def load_model():
    return Llama(
        model_path=r"C:\Users\garv\OneDrive\Desktop\UNITY\Data Science\Deep Learning\Finan\Downloads\mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        n_ctx=1500,
        n_threads=8
    )

llm = load_model()

# --- Utility Functions ---
def extract_from_pdf(uploaded_pdf, output_dir):
    text_data = ""
    tables_data = []

    with pdfplumber.open(uploaded_pdf) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_data += page_text + "\n"

            page_tables = page.extract_tables()
            for table in page_tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                tables_data.append(df)

    with open(f"{output_dir}/itr_text.txt", "w", encoding="utf-8") as f:
        f.write(text_data)

    for i, table_df in enumerate(tables_data):
        table_df.to_csv(f"{output_dir}/table_{i+1}.csv", index=False)

    return text_data, tables_data

def answer_question(itr_text, tables_text, business_context, user_question):
    qa_prompt = f"""
You are a financial assistant AI. Use the extracted Income Tax Return (ITR-1) document, tables, and business context below to answer.

--- OCR Text ---
{itr_text}

--- Extracted Tables ---
{tables_text}

--- Business Context ---
{business_context}

--- User Question ---
{user_question}

Answer clearly, practically, and use ₹ for currency. Be concise but specific.
    """
    response = llm(qa_prompt, max_tokens=500, stop=["</s>"])
    return response["choices"][0]["text"].strip()

# --- Streamlit App UI ---
st.title("📄➡️🤖 Financial Document Q&A Chatbot")

uploaded_pdf = st.file_uploader("Upload your ITR PDF", type="pdf")

if uploaded_pdf:
    filename = uploaded_pdf.name.split(".")[0]
    session_dir = f"sessions/{filename}"

    # Create folder
    os.makedirs(session_dir, exist_ok=True)

    # Save uploaded file temporarily
    uploaded_pdf_path = os.path.join(session_dir, uploaded_pdf.name)
    with open(uploaded_pdf_path, "wb") as f:
        f.write(uploaded_pdf.getbuffer())

    st.success("PDF uploaded. Extracting data...")

    # Extract
    itr_text, tables_data = extract_from_pdf(uploaded_pdf_path, session_dir)

    # Combine all tables
    all_tables_text = "\n\n".join(df.to_string(index=False) for df in tables_data)

    # Business Context
    business_context = st.text_area("✍️ Enter your Business Context", placeholder="Example: I run a textile export business with 15L turnover...")

    if business_context:
        st.success("Business Context noted. You can now ask questions!")

        # Chatbot input
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_input = st.text_input("❓ Ask your question:")

        if user_input:
            with st.spinner("Thinking..."):
                answer = answer_question(itr_text, all_tables_text, business_context, user_input)
                st.session_state.chat_history.append((user_input, answer))

        # Display chat history
        for user_q, bot_a in st.session_state.chat_history:
            st.markdown(f"**You:** {user_q}")
            st.markdown(f"**AI:** {bot_a}")

# --- Cleanup when session ends ---
if st.button("🛑 End Session and Cleanup"):
    try:
        shutil.rmtree(session_dir)
        st.success("Session cleaned up! Folder deleted.")
    except Exception as e:
        st.error(f"Error deleting session: {e}")