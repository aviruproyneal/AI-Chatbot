import io
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

client = OpenAI(
    api_key=st.secrets["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

MODEL_NAME = "deepseek/deepseek-chat"

st.set_page_config(page_title="AI StudyMate", page_icon="📚")
st.title("📚 AI StudyMate")

st.markdown("""
Ask questions, upload PDFs and get clear AI-powered explanations.

Built by Avirup Roy using Python and Streamlit.
""")

with st.sidebar:
    st.header("About this app")
    st.write("""
This app can:

- Answer questions conversationally
- Analyze uploaded PDFs
- Explain complex topics simply
- Use document context when relevant
""")

SYSTEM_PROMPT = """
You are AI StudyMate, an AI assistant created by Avirup Roy.

Your job is to:
- explain concepts clearly
- use simple language first
- give practical answers
- help users understand documents and topics efficiently

If PDF content is provided, use it when relevant.
If the answer is not clearly supported by the PDF, say that clearly.
Do not pretend the PDF contains information that is not there.
"""

st.markdown("""
### 💡 Try asking:
- Summarize this PDF
- Explain this document simply
- What are the main topics?
""")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

pdf_text = ""

if uploaded_file is not None:
    try:
        pdf_bytes = uploaded_file.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

        extracted_pages = []
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)

        pdf_text = "\n\n".join(extracted_pages)
        pdf_text = pdf_text[:12000]

        st.success("PDF uploaded and text extracted successfully")
        st.info(f"Using document: **{uploaded_file.name}**")

    except Exception as e:
        st.error(f"Could not read PDF: {e}")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

if st.button("Clear Chat"):
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    st.rerun()

for msg in st.session_state.messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

user_input = st.chat_input("Ask me anything")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    try:
        messages_to_send = st.session_state.messages.copy()

        if pdf_text.strip():
            pdf_context = f"""
Here is the uploaded PDF content:

{pdf_text}

Use this PDF content when answering if it is relevant.
If the answer is not in the PDF, say that clearly.
"""
            messages_to_send.insert(1, {"role": "system", "content": pdf_context})

        with st.spinner("AI is thinking..."):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_to_send,
                stream=True
            )

            assistant_message = ""
            message_placeholder = st.chat_message("assistant").empty()

            for chunk in response:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if hasattr(delta, "content") and delta.content:
                    assistant_message += delta.content
                    message_placeholder.write(assistant_message)

        if not assistant_message:
            assistant_message = "No response found"

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_message
        })

    except Exception as e:
        st.error(f"Error: {e}")

st.divider()
st.caption("Built by Avirup Roy • Python • Streamlit • OpenRouter")
