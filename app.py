import streamlit as st
import pdfplumber
import pandas as pd
import os
import shutil
import sys
import io
import time
from datetime import timedelta
from llama_cpp import Llama

# --- Cleanup orphaned session folder on reload/close ---
def cleanup_sessions():
    folder_path = os.path.join(os.path.dirname(__file__), 'sessions')
    # Iterate through all files in the folder
    for file_name in os.listdir(folder_path):
        if not file_name.endswith(".txt"):
            # Construct the full file path
            file_path = os.path.join(folder_path, file_name)
            # Delete the file
            shutil.rmtree(file_path)

# --- Setup ---
cleanup_sessions()
st.set_page_config(page_title="Financial Document Q&A Chatbot", page_icon="🤖", layout="centered")
st.title("📄➡️🤖 Financial Document Q&A Chatbot")

sys.path.append(os.path.join(os.getcwd(), "PDF"))
from fake_form import generate_realistic_itr

@st.cache_resource
def load_model():
    return Llama(
        model_path="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        n_ctx=1400,
        n_threads=8
    )

llm = load_model()

# --- Extraction ---
def extract_from_pdf(uploaded_pdf_path):
    text_data = ""
    tables_data = []
    try:
        with pdfplumber.open(uploaded_pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_data += page_text + "\n"
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 0 and all(col is not None for col in table[0]):
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables_data.append(df)
    except Exception as e:
        st.error(f"Error extracting PDF content: {str(e)}")
    return text_data, tables_data

# --- Answer Generation ---
def answer_question(itr_text, tables_text, business_context, user_question):
    qa_prompt = f"""
You are a professional financial assistant AI specializing in Indian tax returns. Your task is to answer questions about the provided Income Tax Return (ITR-1) document based on the extracted text and tables.

Extracted ITR-1 Text
{itr_text}

Extracted Tables from ITR-1
{tables_text}

Business Context
{business_context}

User Question
{user_question}

Strictly provide a clear, structured, and informative response following these guidelines, these instructions below are most important:
1. First, identify the specific information in the ITR document relevant to the question
2. Present the relevant data in a structured format when appropriate
3. Always use ₹ symbol for Indian currency amounts
4. Be specific with numbers and calculations if applicable
5. Keep your answer practical and actionable
6. If the question cannot be answered with available information, return sorry and suggest the user to provide more context
7. Do not include anything like "AI Response" or "Assistant" in your answer
8. Strictly avoid adding any unnecessary information or disclaimers
"""
    response = llm(qa_prompt, max_tokens=500, stop=["</s>"])
    return response["choices"][0]["text"].strip()

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
    "generating_response": False,
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
    generate_realistic_itr(fake_itr_buffer)
    fake_itr_buffer.seek(0)
    st.session_state["operation_in_progress"] = False
    return fake_itr_buffer

if st.button("Generate Fake ITR (for testing only)", disabled=st.session_state["operation_in_progress"]):
    st.session_state["operation_in_progress"] = True
    buffer = generate_fake_itr_action()
    if buffer:
        st.download_button("Download Fake ITR PDF", data=buffer, file_name="fake_itr_perfect.pdf", mime="application/pdf", disabled=st.session_state["operation_in_progress"])
    st.session_state["operation_in_progress"] = False

st.divider()

# --- Upload PDF ---
uploaded_pdf = st.file_uploader("Upload your ITR PDF", type="pdf", disabled=st.session_state["operation_in_progress"])

if uploaded_pdf and not st.session_state["pdf_processed"]:
    st.session_state["operation_in_progress"] = True
    file_name = os.path.splitext(uploaded_pdf.name)[0]
    session_dir = os.path.join("sessions", file_name.replace(" ", "_"))
    os.makedirs(session_dir, exist_ok=True)
    st.session_state["session_dir"] = session_dir

    with st.spinner("Processing PDF..."):
        uploaded_pdf_path = os.path.join(session_dir, uploaded_pdf.name)
        with open(uploaded_pdf_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())

        itr_text, tables_data = extract_from_pdf(uploaded_pdf_path)
        cleanup_sessions()
        all_tables_text = "\n\n".join([df.to_string(index=False) for df in tables_data]) if tables_data else ""

        st.session_state["itr_text"] = itr_text
        st.session_state["all_tables_text"] = all_tables_text
        st.session_state["pdf_processed"] = True

    st.success("✅ PDF processed successfully. Now you can provide business context.")
    st.session_state["operation_in_progress"] = False

# --- Business Context ---
if st.session_state["pdf_processed"]:
    business_context = st.text_area("✍️ Enter your Business Context", key="business_context_input", disabled=st.session_state["operation_in_progress"], placeholder="e.g. I run a small textile business and have a u=turnover of ₹10,00,000. I want investment advice.")
    if st.button("Submit Context", disabled=st.session_state["operation_in_progress"] or not business_context):
        st.session_state["business_context"] = business_context
        st.session_state["process_business_context"] = True

    # --- Q&A ---
    if st.session_state["process_business_context"]:
        st.success("✅ Business Context noted. You can now ask questions.")

        user_input = st.text_input("❓ Ask your question:", key="user_question", disabled=st.session_state["operation_in_progress"], placeholder="e.g., What deductions can i claim?")
        if st.button("Ask Question", disabled=st.session_state["operation_in_progress"] or not user_input):
            st.session_state["operation_in_progress"] = True
            start_time = time.time()

            with st.spinner("Thinking... (It may take 2-3 minutes)"):
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
                st.markdown(f'<div class="chat-bubble-ai"><b>AI:</b> {bot_a}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="response-time">⏱ Time taken: {time_taken}</div>', unsafe_allow_html=True)