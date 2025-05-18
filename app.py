import streamlit as st
import pdfplumber
import pandas as pd
import io
import time
from datetime import timedelta
from huggingface_hub import InferenceClient
import logging

# Suppress pdfplumber CropBox warnings
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

# --- Setup ---
st.set_page_config(page_title="Financial Document Q&A Chatbot", page_icon="🤖", layout="centered")
st.title("📄➡️🤖 Financial Document Q&A Chatbot")

from fake_form import generate_realistic_itr

# Initialize Hugging Face Inference Client
client = InferenceClient(token=st.secrets["HF_API_KEY"])  # Uses token from huggingface-cli login or HF_API_KEY env var

# --- Extraction ---
def extract_from_pdf(pdf_file):
    text_data = ""
    tables_data = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_data += page_text + "\n"
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 0 and all(col is not None for col in table[0]):
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables_data.append(df)
        # Truncate text to ~10,000 characters (~7,500 tokens)
        if len(text_data) > 10000:
            text_data = text_data[:10000] + "\n[Text truncated due to length]"
        # Summarize tables
        tables_summary = ""
        for i, df in enumerate(tables_data):
            rows, cols = df.shape
            tables_summary += f"Table {i+1}: {rows} rows, {cols} columns. Columns: {', '.join(df.columns)}\n"
            # Include first 2 rows as sample
            if rows > 0:
                sample = df.head(2).to_string(index=False)
                tables_summary += f"Sample:\n{sample}\n"
            if len(tables_summary) > 5000:
                tables_summary = tables_summary[:5000] + "\n[Tables truncated due to length]"
                break
    except Exception as e:
        st.error(f"Error extracting PDF content: {str(e)}. Try a different PDF.")
        return "", ""
    return text_data, tables_summary

# --- Answer Generation ---
def answer_question(itr_text, tables_text, business_context, user_question):
    # Estimate tokens (rough: ~1.3 tokens per word, 4 chars per word)
    def estimate_tokens(text):
        return len(text) // 3  # Conservative estimate
    prompt = f"""
You are a financial assistant for Indian tax returns.

ITR-1 Text: {itr_text}
Tables: {tables_text}
Business Context: {business_context}
Question: {user_question}

Follow these ruels strictly:
1. Respond clearly, use ₹, reference ITR/context, say "Sorry, insufficient data" if needed.
2. Do not include "Answer" or "Response" words in your answer.
3. Give a well structured and professional answer, use bullet points if needed.
4. Be concise but specific, avoid unnecessary details.
5. Do not include phrases like "5. Use financial terms, avoid slang. 6. Avoid grammatical errors, use simple and clear language. 7. Use tables, graphs, images, charts to explain complex ideas. 8. Avoid personal opinions, stick to facts and figures. 9. Use examples to illustrate your points. 10. Use reliable sources to back up your claims."
"""
    total_tokens = estimate_tokens(prompt) + 400  # max_new_tokens
    if total_tokens > 32000:
        return "Sorry, PDF content is too large (exceeds token limit). Please upload a smaller PDF or specify a page."
    try:
        response = client.text_generation(
            prompt=prompt,
            model="HuggingFaceH4/zephyr-7b-beta",
            max_new_tokens=400,
            temperature=0.7,
            top_p=0.9
        )
        return response.strip()
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "rate limit" in error_msg:
            return "Sorry, API rate limit exceeded. Please try again later."
        elif "401" in error_msg or "unauthorized" in error_msg:
            return "Sorry, invalid API token. Please check your Hugging Face token."
        else:
            return f"Error generating response: {error_msg}"

# --- Styling ---
st.markdown("""
<style>
.chat-bubble-user {
    background-color: #DCF8C6;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 5px;
    margin-left: 40px;
    text-align: right;
}
.chat-bubble-ai {
    background-color: #F1F0F0;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 5px;
    margin-right: 40px;
    text-align: left;
}
.response-time {
    font-size: 0.8em;
    color: gray;
    text-align: left;
    margin-left: 40px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- Session Init ---
defaults = {
    "generating_fake_itr": False,
    "operation_in_progress": False,
    "process_business_context": False,
    "chat_history": [],
    "pdf_processed": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- Generate Fake ITR ---
st.subheader("Test the System with a Fake ITR")

def generate_fake_itr_action():
    st.session_state["operation_in_progress"] = True
    fake_itr_buffer = io.BytesIO()
    try:
        generate_realistic_itr(fake_itr_buffer)
        fake_itr_buffer.seek(0)
        return fake_itr_buffer
    except Exception as e:
        st.error(f"Error generating fake ITR: {str(e)}")
        return None
    finally:
        st.session_state["operation_in_progress"] = False

if st.button("Generate Fake ITR (for testing only)", disabled=st.session_state["operation_in_progress"]):
    buffer = generate_fake_itr_action()
    if buffer:
        st.download_button("Download Fake ITR PDF", data=buffer, file_name="fake_itr_perfect.pdf", mime="application/pdf", disabled=st.session_state["operation_in_progress"])

st.divider()

# --- Upload PDF ---
uploaded_pdf = st.file_uploader("Upload your ITR PDF", type="pdf", disabled=st.session_state["operation_in_progress"])

if uploaded_pdf and not st.session_state["pdf_processed"]:
    st.session_state["operation_in_progress"] = True
    with st.spinner("Processing PDF..."):
        pdf_buffer = io.BytesIO(uploaded_pdf.getvalue())
        itr_text, tables_summary = extract_from_pdf(pdf_buffer)
        st.session_state["itr_text"] = itr_text
        st.session_state["all_tables_text"] = tables_summary
        st.session_state["pdf_processed"] = True
    st.success("✅ PDF processed successfully. Now you can provide business context.")
    st.session_state["operation_in_progress"] = False

# --- Business Context ---
if st.session_state["pdf_processed"]:
    business_context = st.text_area("✍️ Enter your Business Context", key="business_context_input", disabled=st.session_state["operation_in_progress"], placeholder="e.g. I run a small textile business and have a turnover of ₹10,00,000. I want investment advice.")
    if st.button("Submit Context", disabled=st.session_state["operation_in_progress"] or not business_context):
        st.session_state["business_context"] = business_context
        st.session_state["process_business_context"] = True

    # --- Q&A ---
    if st.session_state["process_business_context"]:
        st.success("✅ Business Context noted. You can now ask questions.")
        user_input = st.text_input("❓ Ask your question:", key="user_question", disabled=st.session_state["operation_in_progress"], placeholder="e.g., What deductions can I claim?")
        if st.button("Ask Question", disabled=st.session_state["operation_in_progress"] or not user_input):
            st.session_state["operation_in_progress"] = True
            start_time = time.time()
            with st.spinner("Thinking... (This may take a few seconds)"):
                st.info("ℹ️ If the answer is wrong or misleading, please press 'Ask Question' again.")
                answer = answer_question(
                    st.session_state["itr_text"],
                    st.session_state["all_tables_text"],
                    st.session_state["business_context"],
                    user_input
                )
            end_time = time.time()
            response_time = timedelta(seconds=round(end_time - start_time))
            st.session_state.chat_history.append((user_input, answer, str(response_time)))
            st.session_state["operation_in_progress"] = False

        if st.session_state.chat_history:
            st.markdown("### 💬 Conversation")
            for user_q, bot_a, time_taken in st.session_state.chat_history:
                st.markdown(f'<div class="chat-bubble-user"><b>You:</b> {user_q}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-bubble-ai"><b>Finan:</b> {bot_a}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="response-time">⏱ Time taken: {time_taken}</div>', unsafe_allow_html=True)