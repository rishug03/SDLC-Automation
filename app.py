import streamlit as st
import pandas as pd
from io import BytesIO
import groq
from brd import (
    extract_text_from_pdf, extract_text_from_docx,
    generate_section_questions, save_questionnaire_to_excel,
    generate_brd_section, save_brd_to_word
)

# === Initialize Groq client ===
client = groq.Client(api_key="YOUR_GROQ_API_KEY")

# === BRD Sections with Prompts ===
brd_sections = {
    "Executive Summary": "Act as a strategic business consultant...",
    "Business Objectives": "Act as a business user...",
    "Scope": "Act as a project manager of an implementation partner...",
    "Technical Data Flow": "Act as a software architect...",
    "Data Sources": "Act as a data engineer...",
    "Business Rules": "Act as a domain expert...",
}

# === Streamlit UI ===
st.set_page_config(page_title="BRD Generator", layout="wide")
st.title("📄 Business Requirement Document Generator")

# === File Upload or Manual Entry ===
col1, col2, col3 = st.columns(3)
with col1:
    sow_file = st.file_uploader("Upload SOW (PDF)", type=["pdf"])
with col2:
    write_mode = st.checkbox("Write Requirements Manually")
with col3:
    basic_qa = st.button("Show Basic Questions")

business_requirement = ""
if sow_file:
    business_requirement = extract_text_from_pdf(sow_file)
elif write_mode:
    business_requirement = st.text_area("Enter Requirements")

# === Optional Summarization ===
if len(business_requirement) > 3000:
    st.warning("Long input detected. Summarizing...")
    summary_prompt = [
        {"role": "system", "content": "Summarize business goals, scope, and tech requirements."},
        {"role": "user", "content": business_requirement}
    ]
    summary_response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=summary_prompt,
        temperature=0.2,
        max_tokens=4096
    )
    business_requirement = summary_response.choices[0].message.content

if basic_qa:
    st.subheader("Basic Questions")
    st.text_input("1. What is the objective of the project?")
    st.text_input("2. What is the scope of the work?")
    st.text_input("3. What are the technical constraints?")
    st.text_input("4. What data sources are used?")
    st.text_input("5. What are the expected deliverables?")

# === Generate Questionnaire ===
if st.button("Generate Questionnaire"):
    if not business_requirement:
        st.warning("Upload or write requirements first.")
    else:
        st.info("Generating section-wise questions... ⏳")
        all_questions = {
            section: generate_section_questions(section, prompt, business_requirement)
            for section, prompt in brd_sections.items()
        }
        excel_data = save_questionnaire_to_excel(all_questions)
        st.download_button("📥 Download Excel", data=excel_data, file_name="questionnaire.xlsx")

# === Upload Answers or Transcripts ===
st.subheader("Step 2: Upload Answers or Meeting Transcripts")
qna_file = st.file_uploader("Upload Answered Questionnaire", type=["xlsx"])
transcript_files = st.file_uploader("Upload Transcripts (DOCX)", type=["docx"], accept_multiple_files=True)

# === Process Transcripts ===
transcript_texts = []
if transcript_files:
    for file in transcript_files:
        text = extract_text_from_docx(file)
        if len(text) > 3000:
            st.warning(f"Summarizing {file.name}...")
            summary_prompt = [
                {"role": "system", "content": "Summarize meeting transcript for BRD insights."},
                {"role": "user", "content": text}
            ]
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=summary_prompt,
                temperature=0.2,
                max_tokens=4096
            )
            text = response.choices[0].message.content
        transcript_texts.append(text)

# === Generate Final BRD ===
if st.button("Generate BRD"):
    if not qna_file:
        st.warning("Upload answered questionnaire first.")
    else:
        df = pd.read_excel(qna_file)
        brd_content = {}

        for section in brd_sections:
            section_df = df[df["Section"] == section]
            qna_text = "\n".join([
                f"Q: {row['Questions']}\nA: {row['Answers']}"
                for _, row in section_df.iterrows()
            ])
            brd_content[section] = generate_brd_section(section, qna_text)

        for transcript in transcript_texts:
            for section, content in brd_content.items():
                update_prompt = [
                    {"role": "system", "content": "Update BRD section using stakeholder meeting insights. Use bullet points."},
                    {"role": "user", "content": f"""Section: {section}
Current content:
{content}

Transcript notes:
{transcript}

Revise with new inputs."""}
                ]
                updated = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=update_prompt,
                    temperature=0.2,
                    max_tokens=4096
                )
                brd_content[section] = updated.choices[0].message.content

        brd_file = save_brd_to_word(brd_content)
        st.success("✅ BRD successfully generated!")
        st.download_button("📄 Download BRD", data=brd_file, file_name="BRD_Final.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
