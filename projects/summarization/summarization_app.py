import streamlit as st
import summarization_lib as glib
import os
import base64

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Document/Text Summarization", layout="wide")

# -----------------------------
# Session state defaults
# -----------------------------
if "uploaded_pdf_path" not in st.session_state:
    st.session_state["uploaded_pdf_path"] = None
if "typed_text" not in st.session_state:
    st.session_state["typed_text"] = ""
if "instruction_text" not in st.session_state:
    st.session_state["instruction_text"] = ""
if "summary_result" not in st.session_state:
    st.session_state["summary_result"] = ""

# -----------------------------
# Reset function
# -----------------------------
def reset_all():
    st.session_state["uploaded_pdf_path"] = None
    st.session_state["typed_text"] = ""
    st.session_state["instruction_text"] = ""
    st.session_state["summary_result"] = ""

# -----------------------------
# Sidebar - frozen header + controls
# -----------------------------
st.sidebar.title("📄 Document/Text Summarization")

# Input type selection
input_method = st.sidebar.radio("Select input type:", ["PDF Upload", "Text Input"], index=0)

# Instructions
st.session_state["instruction_text"] = st.sidebar.text_area(
    "How would you like it summarized?",
    value=st.session_state["instruction_text"]
)

# Buttons
summarize_button = st.sidebar.button("Summarize")
reset_button = st.sidebar.button("Reset", disabled=not (
    st.session_state["uploaded_pdf_path"] or st.session_state["typed_text"].strip() or st.session_state["instruction_text"].strip() or st.session_state["summary_result"].strip()
))

# Reset action
if reset_button:
    reset_all()

# -----------------------------
# Main area
# -----------------------------
# PDF Upload
if input_method == "PDF Upload":
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])
    os.makedirs("uploads", exist_ok=True)

    if uploaded_file is not None:
        file_path = os.path.join("uploads", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state["uploaded_pdf_path"] = file_path
        st.success(f"PDF uploaded: {file_path}")

    # PDF Preview
    if st.session_state["uploaded_pdf_path"] is not None:
        with open(st.session_state["uploaded_pdf_path"], "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f"""
            <iframe src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" height="800px" type="application/pdf"></iframe>
        """
        st.markdown("### 📄 PDF Preview")
        st.markdown(pdf_display, unsafe_allow_html=True)

# Text Input
if input_method == "Text Input":
    st.session_state["typed_text"] = st.text_area(
        "Enter text to summarize",
        height=200,
        value=st.session_state["typed_text"]
    )

# -----------------------------
# Summarization logic
# -----------------------------
if summarize_button:
    # Determine backend input
    if input_method == "Text Input" and st.session_state["typed_text"].strip() != "":
        summary_input = (
            "Summarize this text:\n\n"
            + st.session_state["typed_text"]
            + "\n\n"
            + st.session_state["instruction_text"]
        )
        file_path_arg = None
    elif input_method == "PDF Upload" and st.session_state["uploaded_pdf_path"] is not None:
        summary_input = st.session_state["instruction_text"]
        file_path_arg = st.session_state["uploaded_pdf_path"]
    else:
        st.warning("Please provide input and instructions.")
        summary_input = None
        file_path_arg = None

    if summary_input:
        with st.spinner("Generating summary..."):
            st.session_state["summary_result"] = glib.get_summary(summary_input, file_path=file_path_arg)

# -----------------------------
# Display summary
# -----------------------------
if st.session_state["summary_result"].strip() != "":
    st.markdown("### 📝 Summary")
    with st.expander("View Summary", expanded=True):
        st.markdown(
            f"""
            <div style="
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                font-family: Arial, sans-serif;
                line-height: 1.6;
                white-space: pre-wrap;
            ">
                {st.session_state["summary_result"]}
            </div>
            """,
            unsafe_allow_html=True
        )
        # Copy button
        st.button(
            "📋 Copy Summary",
            key="copy_summary",
            on_click=lambda: st.experimental_set_query_params(summary=st.session_state["summary_result"])
        )
